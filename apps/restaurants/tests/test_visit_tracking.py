"""
Test cases for visit tracking functionality.
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from apps.restaurants.models import (
    Restaurant,
    Cuisine,
    UserRestaurantVisit,
    UserCuisineStat,
)
from apps.restaurants.services.visit_tracking import (
    update_visit_stats,
    get_user_restaurant_stats,
    get_user_cuisine_stats,
    get_user_top_restaurants,
    get_user_top_cuisines,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestUserRestaurantVisitModel:
    """Test cases for UserRestaurantVisit model."""

    @pytest.mark.unit
    def test_visit_creation(self):
        """Test creating a user restaurant visit record."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        restaurant = Restaurant.objects.create(
            place_id="test123", name="Test Restaurant"
        )

        visit = UserRestaurantVisit.objects.create(
            user=user, restaurant=restaurant, visit_count=1
        )

        assert visit.user == user
        assert visit.restaurant == restaurant
        assert visit.visit_count == 1
        assert visit.last_visit is not None

    @pytest.mark.unit
    def test_unique_constraint(self):
        """Test that user-restaurant combination is unique."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        restaurant = Restaurant.objects.create(
            place_id="test123", name="Test Restaurant"
        )

        UserRestaurantVisit.objects.create(
            user=user, restaurant=restaurant, visit_count=1
        )

        with pytest.raises(IntegrityError):
            UserRestaurantVisit.objects.create(
                user=user, restaurant=restaurant, visit_count=2
            )

    @pytest.mark.unit
    def test_str_representation(self):
        """Test string representation of visit."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        restaurant = Restaurant.objects.create(
            place_id="test123", name="Test Restaurant"
        )

        visit = UserRestaurantVisit.objects.create(
            user=user, restaurant=restaurant, visit_count=5
        )

        expected = "test@example.com -> Test Restaurant (5 visits)"
        assert str(visit) == expected


class TestUserCuisineStatModel:
    """Test cases for UserCuisineStat model."""

    @pytest.mark.unit
    def test_cuisine_stat_creation(self):
        """Test creating a user cuisine stat record."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        cuisine = Cuisine.objects.create(name="Italian")

        stat = UserCuisineStat.objects.create(user=user, cuisine=cuisine, visit_count=3)

        assert stat.user == user
        assert stat.cuisine == cuisine
        assert stat.visit_count == 3

    @pytest.mark.unit
    def test_unique_constraint(self):
        """Test that user-cuisine combination is unique."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        cuisine = Cuisine.objects.create(name="Italian")

        UserCuisineStat.objects.create(user=user, cuisine=cuisine, visit_count=1)

        with pytest.raises(IntegrityError):
            UserCuisineStat.objects.create(user=user, cuisine=cuisine, visit_count=2)

    @pytest.mark.unit
    def test_str_representation(self):
        """Test string representation of cuisine stat."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        cuisine = Cuisine.objects.create(name="Italian")

        stat = UserCuisineStat.objects.create(user=user, cuisine=cuisine, visit_count=7)

        expected = "test@example.com -> Italian (7 visits)"
        assert str(stat) == expected


class TestVisitTrackingService:
    """Test cases for visit tracking service functions."""

    @pytest.mark.unit
    def test_update_visit_stats_new_restaurant(self):
        """Test updating visit stats for a new restaurant."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        cuisine = Cuisine.objects.create(name="Italian")
        restaurant = Restaurant.objects.create(
            place_id="test123", name="Test Restaurant"
        )
        restaurant.cuisines.set([cuisine])

        # Update visit stats
        update_visit_stats(user, restaurant, "2023-01-01")

        # Check restaurant visit was created
        restaurant_visit = UserRestaurantVisit.objects.get(
            user=user, restaurant=restaurant
        )
        assert restaurant_visit.visit_count == 1

        # Check cuisine stat was created
        cuisine_stat = UserCuisineStat.objects.get(user=user, cuisine=cuisine)
        assert cuisine_stat.visit_count == 1

    @pytest.mark.unit
    def test_update_visit_stats_existing_restaurant(self):
        """Test updating visit stats for an existing restaurant."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        cuisine = Cuisine.objects.create(name="Italian")
        restaurant = Restaurant.objects.create(
            place_id="test123", name="Test Restaurant"
        )
        restaurant.cuisines.set([cuisine])

        # Create existing visit record
        UserRestaurantVisit.objects.create(
            user=user, restaurant=restaurant, visit_count=2
        )
        UserCuisineStat.objects.create(user=user, cuisine=cuisine, visit_count=2)

        # Update visit stats
        update_visit_stats(user, restaurant, "2023-01-02")

        # Check counts were incremented
        restaurant_visit = UserRestaurantVisit.objects.get(
            user=user, restaurant=restaurant
        )
        assert restaurant_visit.visit_count == 3

        cuisine_stat = UserCuisineStat.objects.get(user=user, cuisine=cuisine)
        assert cuisine_stat.visit_count == 3

    @pytest.mark.unit
    def test_update_visit_stats_multiple_cuisines(self):
        """Test updating visit stats for restaurant with multiple cuisines."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        italian_cuisine = Cuisine.objects.create(name="Italian")
        pizza_cuisine = Cuisine.objects.create(name="Pizza")
        restaurant = Restaurant.objects.create(
            place_id="test123", name="Italian Pizza Restaurant"
        )
        restaurant.cuisines.set([italian_cuisine, pizza_cuisine])

        # Update visit stats
        update_visit_stats(user, restaurant, "2023-01-01")

        # Check both cuisine stats were created
        italian_stat = UserCuisineStat.objects.get(user=user, cuisine=italian_cuisine)
        assert italian_stat.visit_count == 1

        pizza_stat = UserCuisineStat.objects.get(user=user, cuisine=pizza_cuisine)
        assert pizza_stat.visit_count == 1

    @pytest.mark.unit
    def test_get_user_restaurant_stats(self):
        """Test getting user restaurant statistics."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        restaurant1 = Restaurant.objects.create(place_id="test1", name="Restaurant 1")
        restaurant2 = Restaurant.objects.create(place_id="test2", name="Restaurant 2")

        UserRestaurantVisit.objects.create(
            user=user, restaurant=restaurant1, visit_count=5
        )
        UserRestaurantVisit.objects.create(
            user=user, restaurant=restaurant2, visit_count=3
        )

        stats = get_user_restaurant_stats(user)
        assert len(stats) == 2
        # Should be ordered by visit count (descending)
        assert stats[0].restaurant == restaurant1
        assert stats[0].visit_count == 5
        assert stats[1].restaurant == restaurant2
        assert stats[1].visit_count == 3

    @pytest.mark.unit
    def test_get_user_cuisine_stats(self):
        """Test getting user cuisine statistics."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        italian_cuisine = Cuisine.objects.create(name="Italian")
        chinese_cuisine = Cuisine.objects.create(name="Chinese")

        UserCuisineStat.objects.create(
            user=user, cuisine=italian_cuisine, visit_count=8
        )
        UserCuisineStat.objects.create(
            user=user, cuisine=chinese_cuisine, visit_count=4
        )

        stats = get_user_cuisine_stats(user)
        assert len(stats) == 2
        # Should be ordered by visit count (descending)
        assert stats[0].cuisine == italian_cuisine
        assert stats[0].visit_count == 8
        assert stats[1].cuisine == chinese_cuisine
        assert stats[1].visit_count == 4

    @pytest.mark.unit
    def test_get_user_top_restaurants(self):
        """Test getting user's top restaurants."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        restaurant1 = Restaurant.objects.create(place_id="test1", name="Restaurant 1")
        restaurant2 = Restaurant.objects.create(place_id="test2", name="Restaurant 2")

        UserRestaurantVisit.objects.create(
            user=user, restaurant=restaurant1, visit_count=5
        )
        UserRestaurantVisit.objects.create(
            user=user, restaurant=restaurant2, visit_count=3
        )

        top_restaurants = get_user_top_restaurants(user, limit=1)
        assert len(top_restaurants) == 1
        assert top_restaurants[0][0] == restaurant1  # restaurant
        assert top_restaurants[0][1] == 5  # visit_count

    @pytest.mark.unit
    def test_get_user_top_cuisines(self):
        """Test getting user's top cuisines."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        italian_cuisine = Cuisine.objects.create(name="Italian")
        chinese_cuisine = Cuisine.objects.create(name="Chinese")

        UserCuisineStat.objects.create(
            user=user, cuisine=italian_cuisine, visit_count=8
        )
        UserCuisineStat.objects.create(
            user=user, cuisine=chinese_cuisine, visit_count=4
        )

        top_cuisines = get_user_top_cuisines(user, limit=1)
        assert len(top_cuisines) == 1
        assert top_cuisines[0][0] == italian_cuisine  # cuisine
        assert top_cuisines[0][1] == 8  # visit_count

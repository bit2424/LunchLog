"""
Test cases for restaurants models.
"""

import pytest
import uuid
from decimal import Decimal
from django.db import IntegrityError
from apps.restaurants.models import Restaurant, Cuisine

pytestmark = pytest.mark.django_db


class TestCuisineModel:
    """Test cases for Cuisine model."""

    @pytest.mark.unit
    def test_cuisine_creation(self):
        """Test creating a cuisine."""
        cuisine = Cuisine.objects.create(name="Italian")
        assert cuisine.name == "Italian"
        assert str(cuisine) == "Italian"

    @pytest.mark.unit
    def test_cuisine_unique_name(self):
        """Test that cuisine names are unique."""
        Cuisine.objects.create(name="Italian")
        with pytest.raises(IntegrityError):
            Cuisine.objects.create(name="Italian")

    @pytest.mark.unit
    def test_cuisine_ordering(self):
        """Test that cuisines are ordered by name."""
        Cuisine.objects.create(name="Italian")
        Cuisine.objects.create(name="American")
        Cuisine.objects.create(name="Chinese")

        cuisines = list(Cuisine.objects.all())
        names = [c.name for c in cuisines]
        assert names == ["American", "Chinese", "Italian"]


class TestRestaurantModel:
    """Test cases for Restaurant model."""

    @pytest.mark.unit
    def test_restaurant_creation(self):
        """Test basic restaurant creation."""
        restaurant = Restaurant.objects.create(
            place_id="test123",
            name="Test Restaurant",
            address="123 Test St",
            latitude=40.7128,
            longitude=-74.0060,
            rating=Decimal("4.5"),
        )

        assert restaurant.name == "Test Restaurant"
        assert restaurant.rating == Decimal("4.5")
        assert restaurant.latitude == 40.7128
        assert restaurant.longitude == -74.0060
        assert isinstance(restaurant.id, uuid.UUID)

    @pytest.mark.unit
    def test_restaurant_str_representation(self):
        """Test string representation of restaurant."""
        restaurant = Restaurant.objects.create(
            place_id="test123", name="Test Restaurant"
        )
        assert str(restaurant) == "Test Restaurant"

    @pytest.mark.unit
    def test_restaurant_with_cuisines(self):
        """Test restaurant with multiple cuisines."""
        # Create cuisines
        italian_cuisine = Cuisine.objects.create(name="Italian")
        pizza_cuisine = Cuisine.objects.create(name="Pizza")

        # Create restaurant
        restaurant = Restaurant.objects.create(
            place_id="test123", name="Test Restaurant", address="123 Test St"
        )

        # Add cuisines
        restaurant.cuisines.set([italian_cuisine, pizza_cuisine])

        # Test relationships
        assert restaurant.cuisines.count() == 2
        cuisine_names = list(restaurant.cuisines.values_list("name", flat=True))
        assert "Italian" in cuisine_names
        assert "Pizza" in cuisine_names

        # Test reverse relationship
        assert italian_cuisine.restaurants.count() == 1
        assert restaurant in italian_cuisine.restaurants.all()

    @pytest.mark.unit
    def test_unique_place_id(self):
        """Test that place_id is unique."""
        Restaurant.objects.create(place_id="test123", name="First Restaurant")

        with pytest.raises(IntegrityError):
            Restaurant.objects.create(place_id="test123", name="Second Restaurant")

    @pytest.mark.unit
    def test_restaurant_without_cuisines(self):
        """Test restaurant can exist without cuisines."""
        restaurant = Restaurant.objects.create(
            place_id="test123", name="Test Restaurant"
        )

        assert restaurant.cuisines.count() == 0
        assert list(restaurant.cuisines.all()) == []

    @pytest.mark.unit
    def test_restaurant_cuisine_filtering(self):
        """Test filtering restaurants by cuisine."""
        # Create cuisines
        italian_cuisine = Cuisine.objects.create(name="Italian")
        chinese_cuisine = Cuisine.objects.create(name="Chinese")

        # Create restaurants
        italian_restaurant = Restaurant.objects.create(
            place_id="italian123", name="Italian Restaurant"
        )
        italian_restaurant.cuisines.set([italian_cuisine])

        chinese_restaurant = Restaurant.objects.create(
            place_id="chinese123", name="Chinese Restaurant"
        )
        chinese_restaurant.cuisines.set([chinese_cuisine])

        mixed_restaurant = Restaurant.objects.create(
            place_id="mixed123", name="Mixed Restaurant"
        )
        mixed_restaurant.cuisines.set([italian_cuisine, chinese_cuisine])

        # Test filtering
        italian_restaurants = Restaurant.objects.filter(cuisines__name="Italian")
        assert (
            italian_restaurants.count() == 2
        )  # italian_restaurant and mixed_restaurant

        chinese_restaurants = Restaurant.objects.filter(cuisines__name="Chinese")
        assert (
            chinese_restaurants.count() == 2
        )  # chinese_restaurant and mixed_restaurant

        # Test case-insensitive filtering
        italian_case_insensitive = Restaurant.objects.filter(
            cuisines__name__icontains="italian"
        )
        assert italian_case_insensitive.count() == 2

    @pytest.mark.unit
    def test_restaurant_meta_ordering(self):
        """Test that restaurants are ordered by name."""
        Restaurant.objects.create(place_id="z123", name="Zebra Restaurant")
        Restaurant.objects.create(place_id="a123", name="Alpha Restaurant")
        Restaurant.objects.create(place_id="m123", name="Middle Restaurant")

        restaurants = list(Restaurant.objects.all())
        names = [r.name for r in restaurants]
        assert names == ["Alpha Restaurant", "Middle Restaurant", "Zebra Restaurant"]

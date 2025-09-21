"""
Integration tests for receipt creation and visit tracking.
"""

import pytest
from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.receipts.models import Receipt
from apps.restaurants.models import Restaurant, Cuisine, UserRestaurantVisit, UserCuisineStat

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestReceiptVisitIntegration:
    """Test integration between receipt creation and visit tracking."""
    
    @pytest.mark.integration
    def test_receipt_creation_updates_visit_stats(self):
        """Test that creating a receipt automatically updates visit statistics."""
        # Create test data
        user = User.objects.create_user(email='test@example.com', password='test123')
        cuisine = Cuisine.objects.create(name='Italian')
        restaurant = Restaurant.objects.create(
            place_id='test123',
            name='Test Restaurant',
            address='123 Test Street'
        )
        restaurant.cuisines.set([cuisine])
        
        # Create a mock image file
        image_file = SimpleUploadedFile(
            name='test_receipt.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        # Verify no visit stats exist initially
        assert UserRestaurantVisit.objects.filter(user=user, restaurant=restaurant).count() == 0
        assert UserCuisineStat.objects.filter(user=user, cuisine=cuisine).count() == 0
        
        # Create receipt - this should trigger the signal
        receipt = Receipt.objects.create(
            user=user,
            restaurant=restaurant,
            date=date(2023, 1, 1),
            price=Decimal('25.99'),
            image=image_file
        )
        
        # Verify visit stats were created
        restaurant_visit = UserRestaurantVisit.objects.get(user=user, restaurant=restaurant)
        assert restaurant_visit.visit_count == 1
        
        cuisine_stat = UserCuisineStat.objects.get(user=user, cuisine=cuisine)
        assert cuisine_stat.visit_count == 1
        
        # Create another receipt for the same restaurant
        image_file2 = SimpleUploadedFile(
            name='test_receipt2.jpg',
            content=b'fake image content 2',
            content_type='image/jpeg'
        )
        
        receipt2 = Receipt.objects.create(
            user=user,
            restaurant=restaurant,
            date=date(2023, 1, 2),
            price=Decimal('18.50'),
            image=image_file2
        )
        
        # Verify visit stats were incremented
        restaurant_visit.refresh_from_db()
        assert restaurant_visit.visit_count == 2
        
        cuisine_stat.refresh_from_db()
        assert cuisine_stat.visit_count == 2
    
    @pytest.mark.integration
    def test_receipt_creation_multiple_cuisines(self):
        """Test receipt creation with restaurant having multiple cuisines."""
        # Create test data
        user = User.objects.create_user(email='test@example.com', password='test123')
        italian_cuisine = Cuisine.objects.create(name='Italian')
        pizza_cuisine = Cuisine.objects.create(name='Pizza')
        restaurant = Restaurant.objects.create(
            place_id='test123',
            name='Italian Pizza Restaurant',
            address='123 Test Street'
        )
        restaurant.cuisines.set([italian_cuisine, pizza_cuisine])
        
        # Create receipt
        image_file = SimpleUploadedFile(
            name='test_receipt.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        receipt = Receipt.objects.create(
            user=user,
            restaurant=restaurant,
            date=date(2023, 1, 1),
            price=Decimal('30.00'),
            image=image_file
        )
        
        # Verify both cuisine stats were created
        italian_stat = UserCuisineStat.objects.get(user=user, cuisine=italian_cuisine)
        assert italian_stat.visit_count == 1
        
        pizza_stat = UserCuisineStat.objects.get(user=user, cuisine=pizza_cuisine)
        assert pizza_stat.visit_count == 1
        
        # Verify restaurant visit was created
        restaurant_visit = UserRestaurantVisit.objects.get(user=user, restaurant=restaurant)
        assert restaurant_visit.visit_count == 1
    
    @pytest.mark.integration
    def test_receipt_without_restaurant_no_stats(self):
        """Test that receipts without restaurant don't create visit stats."""
        # Create test data
        user = User.objects.create_user(email='test@example.com', password='test123')
        
        # Create receipt without restaurant
        image_file = SimpleUploadedFile(
            name='test_receipt.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        receipt = Receipt.objects.create(
            user=user,
            date=date(2023, 1, 1),
            price=Decimal('25.99'),
            image=image_file
        )
        
        # Verify no visit stats were created
        assert UserRestaurantVisit.objects.filter(user=user).count() == 0
        assert UserCuisineStat.objects.filter(user=user).count() == 0
    
    @pytest.mark.integration
    def test_multiple_users_separate_stats(self):
        """Test that visit stats are properly separated by user."""
        # Create test data
        user1 = User.objects.create_user(email='user1@example.com', password='test123')
        user2 = User.objects.create_user(email='user2@example.com', password='test123')
        cuisine = Cuisine.objects.create(name='Italian')
        restaurant = Restaurant.objects.create(
            place_id='test123',
            name='Test Restaurant',
            address='123 Test Street'
        )
        restaurant.cuisines.set([cuisine])
        
        # Create receipts for both users
        image_file1 = SimpleUploadedFile(
            name='user1_receipt.jpg',
            content=b'fake image content 1',
            content_type='image/jpeg'
        )
        
        image_file2 = SimpleUploadedFile(
            name='user2_receipt.jpg',
            content=b'fake image content 2',
            content_type='image/jpeg'
        )
        
        Receipt.objects.create(
            user=user1,
            restaurant=restaurant,
            date=date(2023, 1, 1),
            price=Decimal('25.99'),
            image=image_file1
        )
        
        Receipt.objects.create(
            user=user2,
            restaurant=restaurant,
            date=date(2023, 1, 1),
            price=Decimal('30.50'),
            image=image_file2
        )
        
        # Verify each user has their own stats
        user1_restaurant_visit = UserRestaurantVisit.objects.get(user=user1, restaurant=restaurant)
        assert user1_restaurant_visit.visit_count == 1
        
        user2_restaurant_visit = UserRestaurantVisit.objects.get(user=user2, restaurant=restaurant)
        assert user2_restaurant_visit.visit_count == 1
        
        user1_cuisine_stat = UserCuisineStat.objects.get(user=user1, cuisine=cuisine)
        assert user1_cuisine_stat.visit_count == 1
        
        user2_cuisine_stat = UserCuisineStat.objects.get(user=user2, cuisine=cuisine)
        assert user2_cuisine_stat.visit_count == 1
        
        # Create another receipt for user1
        image_file3 = SimpleUploadedFile(
            name='user1_receipt2.jpg',
            content=b'fake image content 3',
            content_type='image/jpeg'
        )
        
        Receipt.objects.create(
            user=user1,
            restaurant=restaurant,
            date=date(2023, 1, 2),
            price=Decimal('22.75'),
            image=image_file3
        )
        
        # Verify only user1's stats were incremented
        user1_restaurant_visit.refresh_from_db()
        assert user1_restaurant_visit.visit_count == 2
        
        user2_restaurant_visit.refresh_from_db()
        assert user2_restaurant_visit.visit_count == 1  # unchanged
        
        user1_cuisine_stat.refresh_from_db()
        assert user1_cuisine_stat.visit_count == 2
        
        user2_cuisine_stat.refresh_from_db()
        assert user2_cuisine_stat.visit_count == 1  # unchanged

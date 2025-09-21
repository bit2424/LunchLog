"""
Test cases for restaurants models.
"""

import pytest
from decimal import Decimal
from apps.restaurants.models import Restaurant
from django.db import connection

pytestmark = pytest.mark.django_db


@pytest.mark.unit
def test_restaurant_creation():
    """Test basic restaurant creation."""
    restaurant = Restaurant.objects.create(
        place_id='test123',
        name='Test Restaurant',
        address='123 Test St',
        latitude=Decimal('40.7128'),
        longitude=Decimal('-74.0060'),
        cuisine='Italian',
        rating=Decimal('4.5')
    )
    
    assert restaurant.name == 'Test Restaurant'
    assert restaurant.cuisine == 'Italian'
    assert restaurant.rating == Decimal('4.5')


@pytest.mark.unit
def test_restaurant_str_representation():
    """Test string representation of restaurant."""
    restaurant = Restaurant.objects.create(
        place_id='test123',
        name='Test Restaurant'
    )
    assert str(restaurant) == 'Test Restaurant'

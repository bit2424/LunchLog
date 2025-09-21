import uuid
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from .models import Restaurant, Cuisine

User = get_user_model()


class CuisineModelTest(TestCase):
    """Test cases for Cuisine model."""
    
    def test_cuisine_creation(self):
        """Test creating a cuisine."""
        cuisine = Cuisine.objects.create(name='Italian')
        self.assertEqual(cuisine.name, 'Italian')
        self.assertEqual(str(cuisine), 'Italian')
    
    def test_cuisine_unique_name(self):
        """Test that cuisine names are unique."""
        Cuisine.objects.create(name='Italian')
        with self.assertRaises(Exception):
            Cuisine.objects.create(name='Italian')
    
    def test_cuisine_ordering(self):
        """Test that cuisines are ordered by name."""
        Cuisine.objects.create(name='Italian')
        Cuisine.objects.create(name='American')
        Cuisine.objects.create(name='Chinese')
        
        cuisines = list(Cuisine.objects.all())
        names = [c.name for c in cuisines]
        self.assertEqual(names, ['American', 'Chinese', 'Italian'])


class RestaurantModelTest(TestCase):
    """Test cases for Restaurant model."""
    
    def setUp(self):
        self.restaurant_data = {
            'place_id': 'ChIJN1t_tDeuEmsRUsoyG83frY4',
            'name': 'Test Restaurant',
            'address': '123 Test Street, Test City',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'rating': Decimal('4.5')
        }
        self.italian_cuisine = Cuisine.objects.create(name='Italian')
        self.pizza_cuisine = Cuisine.objects.create(name='Pizza')
    
    def test_restaurant_creation(self):
        """Test creating a restaurant."""
        restaurant = Restaurant.objects.create(**self.restaurant_data)
        restaurant.cuisines.set([self.italian_cuisine, self.pizza_cuisine])
        
        self.assertEqual(restaurant.name, 'Test Restaurant')
        self.assertEqual(restaurant.place_id, 'ChIJN1t_tDeuEmsRUsoyG83frY4')
        self.assertEqual(restaurant.rating, Decimal('4.5'))
        self.assertTrue(isinstance(restaurant.id, uuid.UUID))
        
        # Test cuisines relationship
        self.assertEqual(restaurant.cuisines.count(), 2)
        cuisine_names = list(restaurant.cuisines.values_list('name', flat=True))
        self.assertIn('Italian', cuisine_names)
        self.assertIn('Pizza', cuisine_names)
    
    def test_restaurant_str(self):
        """Test restaurant string representation."""
        restaurant = Restaurant.objects.create(**self.restaurant_data)
        self.assertEqual(str(restaurant), 'Test Restaurant')
    
    def test_unique_place_id(self):
        """Test that place_id is unique."""
        Restaurant.objects.create(**self.restaurant_data)
        with self.assertRaises(Exception):
            Restaurant.objects.create(**self.restaurant_data)


class RestaurantAPITest(APITestCase):
    """Test cases for Restaurant API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        
        self.restaurant_data = {
            'place_id': 'ChIJN1t_tDeuEmsRUsoyG83frY4',
            'name': 'Test Restaurant',
            'address': '123 Test Street, Test City',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'rating': '4.5'
        }
        self.italian_cuisine = Cuisine.objects.create(name='Italian')
        self.french_cuisine = Cuisine.objects.create(name='French')
    
    def test_create_restaurant(self):
        """Test creating a restaurant via API."""
        url = '/api/v1/restaurants/'
        response = self.client.post(url, self.restaurant_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Restaurant.objects.count(), 1)
        restaurant = Restaurant.objects.first()
        self.assertEqual(restaurant.name, 'Test Restaurant')
    
    def test_list_restaurants(self):
        """Test listing restaurants."""
        restaurant = Restaurant.objects.create(
            place_id='ChIJN1t_tDeuEmsRUsoyG83frY4',
            name='Test Restaurant',
            address='123 Test Street, Test City',
            latitude=40.7128,
            longitude=-74.0060,
            rating=Decimal('4.5')
        )
        restaurant.cuisines.set([self.italian_cuisine])
        
        url = '/api/v1/restaurants/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Restaurant')
    
    def test_retrieve_restaurant(self):
        """Test retrieving a specific restaurant."""
        restaurant = Restaurant.objects.create(
            place_id='ChIJN1t_tDeuEmsRUsoyG83frY4',
            name='Test Restaurant',
            address='123 Test Street, Test City',
            latitude=40.7128,
            longitude=-74.0060,
            rating=Decimal('4.5')
        )
        restaurant.cuisines.set([self.italian_cuisine])
        
        url = f'/api/v1/restaurants/{restaurant.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Restaurant')
    
    def test_update_restaurant(self):
        """Test updating a restaurant."""
        restaurant = Restaurant.objects.create(
            place_id='ChIJN1t_tDeuEmsRUsoyG83frY4',
            name='Test Restaurant',
            address='123 Test Street, Test City',
            latitude=40.7128,
            longitude=-74.0060,
            rating=Decimal('4.5')
        )
        restaurant.cuisines.set([self.italian_cuisine])
        
        updated_data = self.restaurant_data.copy()
        updated_data['name'] = 'Updated Restaurant'
        
        url = f'/api/v1/restaurants/{restaurant.id}/'
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        restaurant.refresh_from_db()
        self.assertEqual(restaurant.name, 'Updated Restaurant')
    
    def test_delete_restaurant(self):
        """Test deleting a restaurant."""
        restaurant = Restaurant.objects.create(
            place_id='ChIJN1t_tDeuEmsRUsoyG83frY4',
            name='Test Restaurant',
            address='123 Test Street, Test City',
            latitude=40.7128,
            longitude=-74.0060,
            rating=Decimal('4.5')
        )
        restaurant.cuisines.set([self.italian_cuisine])
        
        url = f'/api/v1/restaurants/{restaurant.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Restaurant.objects.count(), 0)
    
    def test_filter_by_cuisine(self):
        """Test filtering restaurants by cuisine."""
        italian_restaurant = Restaurant.objects.create(
            place_id='place1',
            name='Italian Restaurant',
            address='123 Test Street'
        )
        italian_restaurant.cuisines.set([self.italian_cuisine])
        
        french_restaurant = Restaurant.objects.create(
            place_id='place2',
            name='French Restaurant',
            address='456 Test Avenue'
        )
        french_restaurant.cuisines.set([self.french_cuisine])
        
        url = '/api/v1/restaurants/'
        response = self.client.get(url + '?cuisine=Italian')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Italian Restaurant')
    
    def test_filter_by_name(self):
        """Test filtering restaurants by name."""
        pizza_restaurant = Restaurant.objects.create(
            place_id='place1',
            name='Pizza Palace',
            address='123 Test Street'
        )
        pizza_restaurant.cuisines.set([self.italian_cuisine])
        
        american_cuisine = Cuisine.objects.create(name='American')
        burger_restaurant = Restaurant.objects.create(
            place_id='place2',
            name='Burger Joint',
            address='456 Test Avenue'
        )
        burger_restaurant.cuisines.set([american_cuisine])
        
        url = '/api/v1/restaurants/'
        response = self.client.get(url + '?name=Pizza')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Pizza Palace')
    
    def test_search_restaurants(self):
        """Test searching restaurants."""
        pizza_restaurant = Restaurant.objects.create(
            place_id='place1',
            name='Delicious Pizza',
            address='123 Pizza Street'
        )
        pizza_restaurant.cuisines.set([self.italian_cuisine])
        
        american_cuisine = Cuisine.objects.create(name='American')
        burger_restaurant = Restaurant.objects.create(
            place_id='place2',
            name='Burger Joint',
            address='456 Test Avenue'
        )
        burger_restaurant.cuisines.set([american_cuisine])
        
        url = '/api/v1/restaurants/'
        response = self.client.get(url + '?search=Pizza')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the API."""
        self.client.credentials()  # Remove authentication
        url = '/api/v1/restaurants/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

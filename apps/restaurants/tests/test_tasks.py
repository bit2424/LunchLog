import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from celery.result import AsyncResult

from apps.restaurants.models import Restaurant
from apps.restaurants.tasks import update_restaurant_info, update_all_restaurants, create_restaurant_from_places_data
from apps.restaurants.services import GooglePlacesService


class RestaurantTasksTest(TestCase):
    """Test cases for restaurant Celery tasks."""
    
    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            place_id='ChIJN1t_tDeuEmsRUsoyG83frY4',
            name='Test Restaurant',
            address='123 Test Street, Test City',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060'),
            cuisine='Italian',
            rating=Decimal('4.5')
        )
        
        self.mock_places_data = {
            'place_id': 'ChIJN1t_tDeuEmsRUsoyG83frY4',
            'name': 'Updated Restaurant Name',
            'address': '456 Updated Street, Test City',
            'latitude': Decimal('40.7500'),
            'longitude': Decimal('-74.0100'),
            'cuisine': 'French',
            'rating': Decimal('4.8'),
            'business_status': 'OPERATIONAL'
        }
    
    @patch('apps.restaurants.tasks.GooglePlacesService')
    def test_update_restaurant_info_success(self, mock_service_class):
        """Test successful restaurant info update."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.fetch_restaurant_details.return_value = self.mock_places_data
        mock_service_class.return_value = mock_service
        
        # Call the task
        result = update_restaurant_info(str(self.restaurant.id))
        
        # Verify the result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['restaurant_id'], str(self.restaurant.id))
        self.assertIn('name', result['updated_fields'])
        self.assertIn('address', result['updated_fields'])
        
        # Verify the restaurant was updated
        self.restaurant.refresh_from_db()
        self.assertEqual(self.restaurant.name, 'Updated Restaurant Name')
        self.assertEqual(self.restaurant.cuisine, 'French')
        self.assertEqual(self.restaurant.rating, Decimal('4.8'))
    
    @patch('apps.restaurants.tasks.GooglePlacesService')
    def test_update_restaurant_info_no_data(self, mock_service_class):
        """Test restaurant update when no data is returned from Google Places."""
        # Mock the service to return None
        mock_service = MagicMock()
        mock_service.fetch_restaurant_details.return_value = None
        mock_service_class.return_value = mock_service
        
        # Call the task
        result = update_restaurant_info(str(self.restaurant.id))
        
        # Verify the result
        self.assertEqual(result['status'], 'error')
        self.assertIn('Failed to fetch data', result['message'])
    
    def test_update_restaurant_info_not_found(self):
        """Test restaurant update when restaurant doesn't exist."""
        non_existent_id = str(uuid.uuid4())
        
        # Call the task
        result = update_restaurant_info(non_existent_id)
        
        # Verify the result
        self.assertEqual(result['status'], 'error')
        self.assertIn('Restaurant not found', result['message'])
    
    @patch('apps.restaurants.tasks.update_restaurant_info.delay')
    def test_update_all_restaurants(self, mock_update_task):
        """Test update all restaurants task."""
        # Create another restaurant
        Restaurant.objects.create(
            place_id='ChIJAnother_place_id',
            name='Another Restaurant',
            address='789 Another Street'
        )
        
        # Call the task
        result = update_all_restaurants()
        
        # Verify the result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['total_processed'], 2)
        self.assertEqual(mock_update_task.call_count, 2)
    
    @patch('apps.restaurants.tasks.GooglePlacesService')
    def test_create_restaurant_from_places_data_success(self, mock_service_class):
        """Test creating restaurant from Google Places data."""
        # Mock the service
        mock_service = MagicMock()
        mock_service.fetch_restaurant_details.return_value = self.mock_places_data
        mock_service_class.return_value = mock_service
        
        # Call the task
        place_id = 'ChIJNew_place_id'
        result = create_restaurant_from_places_data(place_id, 'Fallback Name', 'Fallback Address')
        
        # Verify a restaurant was created
        self.assertIsNotNone(result)
        restaurant = Restaurant.objects.get(id=result)
        self.assertEqual(restaurant.place_id, place_id)
        self.assertEqual(restaurant.name, 'Updated Restaurant Name')  # From mock data
    
    @patch('apps.restaurants.tasks.GooglePlacesService')
    def test_create_restaurant_from_places_data_fallback(self, mock_service_class):
        """Test creating restaurant with fallback data when Google Places fails."""
        # Mock the service to return None
        mock_service = MagicMock()
        mock_service.fetch_restaurant_details.return_value = None
        mock_service_class.return_value = mock_service
        
        # Call the task
        place_id = 'ChIJNew_place_id'
        result = create_restaurant_from_places_data(place_id, 'Fallback Name', 'Fallback Address')
        
        # Verify a restaurant was created with fallback data
        self.assertIsNotNone(result)
        restaurant = Restaurant.objects.get(id=result)
        self.assertEqual(restaurant.place_id, place_id)
        self.assertEqual(restaurant.name, 'Fallback Name')
        self.assertEqual(restaurant.address, 'Fallback Address')
    
    def test_create_restaurant_existing_place_id(self):
        """Test creating restaurant when place_id already exists."""
        # Try to create restaurant with existing place_id
        result = create_restaurant_from_places_data(
            self.restaurant.place_id, 
            'Another Name', 
            'Another Address'
        )
        
        # Should return existing restaurant ID
        self.assertEqual(result, str(self.restaurant.id))
        
        # Should not create a new restaurant
        self.assertEqual(Restaurant.objects.count(), 1)


class GooglePlacesServiceTest(TestCase):
    """Test cases for Google Places service."""
    
    def setUp(self):
        self.service = GooglePlacesService()
    
    def test_extract_cuisine_from_types(self):
        """Test cuisine extraction from Google Place types."""
        # Test specific cuisine types
        types = ['restaurant', 'italian_restaurant', 'food']
        cuisine = self.service._extract_cuisine_from_types(types)
        self.assertEqual(cuisine, 'Italian')
        
        # Test generic restaurant type
        types = ['restaurant', 'food', 'establishment']
        cuisine = self.service._extract_cuisine_from_types(types)
        self.assertEqual(cuisine, 'Restaurant')
        
        # Test no restaurant types
        types = ['store', 'establishment']
        cuisine = self.service._extract_cuisine_from_types(types)
        self.assertIsNone(cuisine)
    
    @patch('googlemaps.Client')
    def test_fetch_restaurant_details_success(self, mock_client_class):
        """Test successful restaurant details fetch."""
        # Mock the Google Maps client
        mock_client = MagicMock()
        mock_client.place.return_value = {
            'status': 'OK',
            'result': {
                'place_id': 'ChIJN1t_tDeuEmsRUsoyG83frY4',
                'name': 'Test Restaurant',
                'formatted_address': '123 Test Street, Test City',
                'geometry': {
                    'location': {
                        'lat': 40.7128,
                        'lng': -74.0060
                    }
                },
                'rating': 4.5,
                'types': ['restaurant', 'italian_restaurant'],
                'business_status': 'OPERATIONAL'
            }
        }
        mock_client_class.return_value = mock_client
        
        # Create service with mocked client
        service = GooglePlacesService()
        
        # Fetch details
        result = service.fetch_restaurant_details('ChIJN1t_tDeuEmsRUsoyG83frY4')
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'Test Restaurant')
        self.assertEqual(result['cuisine'], 'Italian')
        self.assertEqual(result['rating'], Decimal('4.5'))
    
    @patch('googlemaps.Client')
    def test_fetch_restaurant_details_api_error(self, mock_client_class):
        """Test handling of Google Places API errors."""
        # Mock the Google Maps client to return error
        mock_client = MagicMock()
        mock_client.place.return_value = {
            'status': 'NOT_FOUND',
            'result': {}
        }
        mock_client_class.return_value = mock_client
        
        # Create service with mocked client
        service = GooglePlacesService()
        
        # Fetch details
        result = service.fetch_restaurant_details('ChIJInvalid_place_id')
        
        # Should return None for errors
        self.assertIsNone(result)

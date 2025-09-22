"""
Test cases for restaurant recommendation functionality.
"""

import pytest
from unittest.mock import Mock, patch
from django.contrib.auth import get_user_model
from apps.restaurants.models import Restaurant, Cuisine, UserRestaurantVisit, UserCuisineStat
from apps.restaurants.services.recommendations import RestaurantRecommendationService
from apps.restaurants.services import GooglePlacesService

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestRestaurantRecommendationService:
    """Test cases for RestaurantRecommendationService."""
    
    @pytest.fixture
    def user(self):
        """Create a test user."""
        return User.objects.create_user(email='test@example.com', password='test123')
    
    @pytest.fixture
    def setup_user_data(self, user):
        """Set up test data for the user."""
        # Create cuisines
        italian_cuisine = Cuisine.objects.create(name='Italian')
        chinese_cuisine = Cuisine.objects.create(name='Chinese')
        
        # Create restaurants with coordinates
        restaurant1 = Restaurant.objects.create(
            place_id='place1',
            name='User Favorite Italian',
            address='123 Test St',
            latitude=40.7128,
            longitude=-74.0060
        )
        restaurant1.cuisines.set([italian_cuisine])
        
        restaurant2 = Restaurant.objects.create(
            place_id='place2',
            name='User Favorite Chinese',
            address='456 Test Ave',
            latitude=40.7589,
            longitude=-73.9851
        )
        restaurant2.cuisines.set([chinese_cuisine])
        
        # Create visit history
        UserRestaurantVisit.objects.create(user=user, restaurant=restaurant1, visit_count=5)
        UserRestaurantVisit.objects.create(user=user, restaurant=restaurant2, visit_count=3)
        
        # Create cuisine stats
        UserCuisineStat.objects.create(user=user, cuisine=italian_cuisine, visit_count=5)
        UserCuisineStat.objects.create(user=user, cuisine=chinese_cuisine, visit_count=3)
        
        return {
            'cuisines': [italian_cuisine, chinese_cuisine],
            'restaurants': [restaurant1, restaurant2]
        }
    
    @pytest.mark.unit
    def test_get_user_frequent_locations(self, user, setup_user_data):
        """Test getting user's frequent locations."""
        service = RestaurantRecommendationService()
        locations = service.get_user_frequent_locations(user, limit=5)
        
        assert len(locations) == 2
        assert locations[0]['restaurant_name'] == 'User Favorite Italian'
        assert locations[0]['visit_count'] == 5
        assert locations[0]['latitude'] == 40.7128
        assert locations[0]['longitude'] == -74.0060
        
        assert locations[1]['restaurant_name'] == 'User Favorite Chinese'
        assert locations[1]['visit_count'] == 3
    
    @pytest.mark.unit
    def test_get_user_top_cuisines(self, user, setup_user_data):
        """Test getting user's top cuisines."""
        service = RestaurantRecommendationService()
        cuisines = service.get_user_top_cuisines(user, limit=5)
        
        assert len(cuisines) == 2
        assert cuisines[0] == 'Italian'  # Higher visit count
        assert cuisines[1] == 'Chinese'
    
    @pytest.mark.unit
    @patch.object(GooglePlacesService, 'get_recommendations_near_location')
    def test_get_good_restaurants_recommendations(self, mock_recommendations, user, setup_user_data):
        """Test getting good restaurant recommendations."""
        # Mock the Google Places response with different results for each call
        mock_recommendations.side_effect = [
            [
                {
                    'place_id': 'rec1',
                    'name': 'Great Italian Place',
                    'rating': 4.5,
                    'vicinity': 'Near User Favorite Italian',
                    'cuisines': ['Italian Restaurant']
                }
            ],
            [
                {
                    'place_id': 'rec2',
                    'name': 'Excellent Chinese Restaurant',
                    'rating': 4.8,
                    'vicinity': 'Near User Favorite Chinese',
                    'cuisines': ['Chinese Restaurant']
                }
            ]
        ]
        
        service = RestaurantRecommendationService()
        recommendations = service.get_good_restaurants_recommendations(user, limit=10)
        
        # Verify recommendations were returned
        assert len(recommendations) == 2  # 1 from each location
        
        # Verify mock was called with correct parameters
        assert mock_recommendations.call_count == 2  # Called for each frequent location
        
        # Check first call (most visited restaurant)
        first_call = mock_recommendations.call_args_list[0]
        assert first_call[1]['latitude'] == 40.7128
        assert first_call[1]['longitude'] == -74.0060
        assert first_call[1]['recommendation_type'] == 'good'
        
        # Verify recommendations have reference location info
        for rec in recommendations:
            assert 'reference_location' in rec
            assert 'recommendation_type' in rec
            assert rec['recommendation_type'] == 'good'
    
    @pytest.mark.unit
    @patch.object(GooglePlacesService, 'get_recommendations_near_location')
    def test_get_cheap_restaurants_recommendations(self, mock_recommendations, user, setup_user_data):
        """Test getting cheap restaurant recommendations."""
        mock_recommendations.side_effect = [
            [
                {
                    'place_id': 'cheap1',
                    'name': 'Budget Italian',
                    'rating': 3.8,
                    'price_level': 1,
                    'vicinity': 'Near User Favorite Italian',
                    'cuisines': ['Italian Restaurant']
                }
            ],
            [
                {
                    'place_id': 'cheap2',
                    'name': 'Budget Chinese',
                    'rating': 3.5,
                    'price_level': 1,
                    'vicinity': 'Near User Favorite Chinese',
                    'cuisines': ['Chinese Restaurant']
                }
            ]
        ]
        
        service = RestaurantRecommendationService()
        recommendations = service.get_cheap_restaurants_recommendations(user, limit=10)
        
        assert len(recommendations) == 2  # 1 from each location
        assert mock_recommendations.call_count == 2
        
        # Check recommendation type
        first_call = mock_recommendations.call_args_list[0]
        assert first_call[1]['recommendation_type'] == 'cheap'
        
        # Verify recommendations have correct type
        for rec in recommendations:
            assert rec['recommendation_type'] == 'cheap'
    
    @pytest.mark.unit
    @patch.object(GooglePlacesService, 'get_recommendations_near_location')
    def test_get_cuisine_match_recommendations(self, mock_recommendations, user, setup_user_data):
        """Test getting cuisine-matching restaurant recommendations."""
        mock_recommendations.side_effect = [
            [
                {
                    'place_id': 'match1',
                    'name': 'New Italian Spot',
                    'rating': 4.2,
                    'vicinity': 'Near User Favorite Italian',
                    'cuisines': ['Italian Restaurant', 'Pizza Restaurant']
                }
            ],
            [
                {
                    'place_id': 'match2',
                    'name': 'New Chinese Spot',
                    'rating': 4.0,
                    'vicinity': 'Near User Favorite Chinese',
                    'cuisines': ['Chinese Restaurant', 'Asian Restaurant']
                }
            ]
        ]
        
        service = RestaurantRecommendationService()
        recommendations = service.get_cuisine_match_recommendations(user, limit=10)
        
        assert len(recommendations) == 2  # 1 from each location
        assert mock_recommendations.call_count == 2
        
        # Check recommendation type and cuisine matching
        first_call = mock_recommendations.call_args_list[0]
        assert first_call[1]['recommendation_type'] == 'cuisine_match'
        assert 'Italian' in first_call[1]['user_cuisines']
        assert 'Chinese' in first_call[1]['user_cuisines']
        
        # Verify recommendations have matched cuisines
        for rec in recommendations:
            assert rec['recommendation_type'] == 'cuisine_match'
            assert 'matched_cuisines' in rec
    
    @pytest.mark.unit
    def test_deduplicate_recommendations(self):
        """Test deduplication of recommendations."""
        service = RestaurantRecommendationService()
        
        recommendations = [
            {'place_id': 'place1', 'name': 'Restaurant A'},
            {'place_id': 'place2', 'name': 'Restaurant B'},
            {'place_id': 'place1', 'name': 'Restaurant A Duplicate'},  # Duplicate
            {'place_id': 'place3', 'name': 'Restaurant C'},
        ]
        
        unique_recommendations = service._deduplicate_recommendations(recommendations)
        
        assert len(unique_recommendations) == 3
        place_ids = [rec['place_id'] for rec in unique_recommendations]
        assert place_ids == ['place1', 'place2', 'place3']
    
    @pytest.mark.unit
    def test_get_matching_cuisines(self):
        """Test matching cuisines between restaurant and user preferences."""
        service = RestaurantRecommendationService()
        
        restaurant_cuisines = ['Italian Restaurant', 'Pizza Restaurant', 'Fine Dining Restaurant']
        user_cuisines = ['Italian', 'Chinese', 'Mexican']
        
        matching = service._get_matching_cuisines(restaurant_cuisines, user_cuisines)
        
        assert len(matching) == 1
        assert 'Italian Restaurant' in matching
    
    @pytest.mark.unit
    def test_no_frequent_locations(self, user):
        """Test recommendations when user has no frequent locations."""
        service = RestaurantRecommendationService()
        
        recommendations = service.get_good_restaurants_recommendations(user)
        assert recommendations == []
        
        recommendations = service.get_cheap_restaurants_recommendations(user)
        assert recommendations == []
        
        recommendations = service.get_cuisine_match_recommendations(user)
        assert recommendations == []
    
    @pytest.mark.unit
    @patch.object(GooglePlacesService, 'get_recommendations_near_location')
    def test_get_all_recommendations(self, mock_recommendations, user, setup_user_data):
        """Test getting all recommendation types."""
        mock_recommendations.return_value = [
            {
                'place_id': 'test1',
                'name': 'Test Restaurant',
                'rating': 4.0,
                'vicinity': 'Test Area',
                'cuisines': ['Italian Restaurant']
            }
        ]
        
        service = RestaurantRecommendationService()
        all_recommendations = service.get_all_recommendations(user, limit_per_type=5)
        
        assert 'good' in all_recommendations
        assert 'cheap' in all_recommendations
        assert 'cuisine_match' in all_recommendations
        
        # Each type should have recommendations
        assert len(all_recommendations['good']) > 0
        assert len(all_recommendations['cheap']) > 0
        assert len(all_recommendations['cuisine_match']) > 0


class TestGooglePlacesServiceExtensions:
    """Test cases for extended Google Places service functionality."""
    
    @pytest.mark.unit
    @patch('googlemaps.Client')
    def test_search_nearby_restaurants(self, mock_client_class):
        """Test searching for nearby restaurants with filters."""
        # Mock the Google Maps client
        mock_client = Mock()
        mock_client.places_nearby.return_value = {
            'results': [
                {
                    'place_id': 'place1',
                    'name': 'Great Restaurant',
                    'rating': 4.5,
                    'price_level': 2,
                    'vicinity': '123 Test St',
                    'types': ['restaurant', 'italian_restaurant'],
                    'geometry': {'location': {'lat': 40.7128, 'lng': -74.0060}},
                    'business_status': 'OPERATIONAL'
                },
                {
                    'place_id': 'place2',
                    'name': 'Cheap Eats',
                    'rating': 3.5,
                    'price_level': 1,
                    'vicinity': '456 Test Ave',
                    'types': ['restaurant', 'fast_food_restaurant'],
                    'geometry': {'location': {'lat': 40.7129, 'lng': -74.0061}},
                    'business_status': 'OPERATIONAL'
                }
            ]
        }
        mock_client_class.return_value = mock_client
        service = GooglePlacesService(client=mock_client)
        
        # Test filtering by rating
        results = service.search_nearby_restaurants(
            latitude=40.7128,
            longitude=-74.0060,
            min_rating=4.0
        )
        
        assert len(results) == 1
        assert results[0]['name'] == 'Great Restaurant'
        assert results[0]['rating'] == 4.5
        
        # Test filtering by price level
        results = service.search_nearby_restaurants(
            latitude=40.7128,
            longitude=-74.0060,
            max_price_level=1
        )
        
        assert len(results) == 1
        assert results[0]['name'] == 'Cheap Eats'
        assert results[0]['price_level'] == 1
    
    @pytest.mark.unit
    @patch('googlemaps.Client')
    def test_get_recommendations_near_location(self, mock_client_class):
        """Test getting recommendations near a specific location."""
        mock_client = Mock()
        mock_client.places_nearby.return_value = {
            'results': [
                {
                    'place_id': 'good_place',
                    'name': 'Excellent Restaurant',
                    'rating': 4.8,
                    'vicinity': 'Great location',
                    'types': ['restaurant'],
                    'geometry': {'location': {'lat': 40.7128, 'lng': -74.0060}},
                    'business_status': 'OPERATIONAL'
                }
            ]
        }
        mock_client_class.return_value = mock_client
        
        service = GooglePlacesService(client=mock_client)
        
        # Test 'good' recommendations
        results = service.get_recommendations_near_location(
            latitude=40.7128,
            longitude=-74.0060,
            recommendation_type='good'
        )
        
        assert len(results) == 1
        assert results[0]['name'] == 'Excellent Restaurant'
        
        # Verify the places_nearby was called with correct parameters
        mock_client.places_nearby.assert_called_with(
            location=(40.7128, -74.0060),
            radius=2000,
            type='restaurant'
        )

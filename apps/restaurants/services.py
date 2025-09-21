import logging
from typing import Dict, Optional
from decimal import Decimal

import googlemaps
from django.conf import settings

logger = logging.getLogger(__name__)


class GooglePlacesService:
    """Service for interacting with Google Places API."""
    
    def __init__(self, client: Optional[googlemaps.Client] = None):
        """
        Initialize the Google Places service.

        Accepts an optional pre-configured googlemaps.Client for test purposes.
        """
        if client is not None:
            self.client = client
            return

        api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', None)
        if not api_key or not isinstance(api_key, str):
            if api_key:
                logger.warning("Google Places API key appears invalid; client disabled for safety")
            else:
                logger.warning("Google Places API key not configured; client disabled")
            self.client = None
            return

        try:
            self.client = googlemaps.Client(key=api_key)
        except Exception as exc:
            logger.warning(f"Failed to initialize Google Places client: {exc}")
            self.client = None
    
    def fetch_restaurant_details(self, place_id: str) -> Optional[Dict]:
        """
        Fetch restaurant details from Google Places API.
        
        Args:
            place_id: Google Places place_id
            
        Returns:
            Dictionary with restaurant data or None if error
        """
        if not self.client:
            logger.error("Google Places client not initialized")
            return None
        
        try:
            # Fields to retrieve from Google Places API
            fields = [
                'place_id',
                'name',
                'formatted_address',
                'geometry',
                'rating',
                'business_status',
                'type'
            ]
            
            result = self.client.place(
                place_id=place_id,
                fields=fields
            )
            
            if result.get('status') != 'OK':
                logger.error(f"Google Places API error: {result.get('status')}")
                return None
            
            print("--------------------------------")
            print("RAW Result from Google Places API:")
            print(result)
            print("--------------------------------")
            
            place_data = result.get('result', {})
            
            # Extract geometry data
            geometry = place_data.get('geometry', {})
            location = geometry.get('location', {})
            
            # Extract cuisine type from Google Place types
            place_types = place_data.get('types') or []
            # Some APIs expose singular 'type'
            if not place_types and place_data.get('type'):
                place_types = [place_data.get('type')]
            cuisine = self._extract_cuisine_from_types(place_types)
            
            return {
                'place_id': place_data.get('place_id'),
                'name': place_data.get('name'),
                'address': place_data.get('formatted_address'),
                'latitude': Decimal(str(location.get('lat', 0))) if location.get('lat') else None,
                'longitude': Decimal(str(location.get('lng', 0))) if location.get('lng') else None,
                'rating': Decimal(str(place_data.get('rating', 0))) if place_data.get('rating') else None,
                'cuisine': cuisine,
                'business_status': place_data.get('business_status', 'UNKNOWN')
            }
            
        except Exception as e:
            logger.error(f"Error fetching place details for {place_id}: {str(e)}")
            return None
    
    def find_place_from_text(self, text_query: str) -> Optional[Dict]:
        """
        Find a place by free-text query using Google Places.
        
        Args:
            text_query: Text describing the place (e.g., "Joe's Pizza, 7 Carmine St, New York, NY")
        
        Returns:
            A minimal candidate dict with keys: place_id, name, formatted_address, geometry; or None if not found.
        """
        if not self.client:
            logger.error("Google Places client not initialized")
            return None
        
        try:
            # Use the Places API Find Place endpoint for robust text queries
            result = self.client.find_place(
                input=text_query,
                input_type='textquery',
                fields=['place_id', 'name', 'formatted_address', 'geometry']
            )
            candidates = result.get('candidates', []) if isinstance(result, dict) else []
            if not candidates:
                logger.info(f"No candidates found for text query: {text_query}")
                return None
            candidate = candidates[0]
            return {
                'place_id': candidate.get('place_id'),
                'name': candidate.get('name'),
                'formatted_address': candidate.get('formatted_address') or candidate.get('formatted_address'),
                'geometry': candidate.get('geometry')
            }
        except Exception as e:
            logger.error(f"Error finding place from text '{text_query}': {str(e)}")
            return None
    
    def _extract_cuisine_from_types(self, types: list) -> Optional[str]:
        """
        Extract cuisine type from Google Places types.
        
        Args:
            types: List of Google Place types
            
        Returns:
            Cuisine type string or None
        """
        # Map Google Place types to cuisine types
        cuisine_map = {
            'bakery': 'Bakery',
            'bar': 'Bar',
            'cafe': 'Cafe',
            'meal_delivery': 'Delivery',
            'meal_takeaway': 'Takeaway',
            'restaurant': 'Restaurant',
            'food': 'Food',
            # Specific cuisine types
            'chinese_restaurant': 'Chinese',
            'indian_restaurant': 'Indian',
            'italian_restaurant': 'Italian',
            'japanese_restaurant': 'Japanese',
            'mexican_restaurant': 'Mexican',
            'thai_restaurant': 'Thai',
            'french_restaurant': 'French',
            'korean_restaurant': 'Korean',
            'vietnamese_restaurant': 'Vietnamese',
            'greek_restaurant': 'Greek',
            'spanish_restaurant': 'Spanish',
            'turkish_restaurant': 'Turkish',
            'american_restaurant': 'American',
            'seafood_restaurant': 'Seafood',
            'steak_house': 'Steakhouse',
            'sushi_restaurant': 'Sushi',
            'pizza_restaurant': 'Pizza',
            'sandwich_shop': 'Sandwiches',
            'hamburger_restaurant': 'Burgers',
            'fast_food_restaurant': 'Fast Food',
        }
        
        # Look for specific cuisine types first
        for type_name in types:
            if type_name in cuisine_map:
                cuisine = cuisine_map[type_name]
                if cuisine != 'Restaurant' and cuisine != 'Food':  # Skip generic types
                    return cuisine
        
        # Fall back to generic restaurant types
        for type_name in types:
            if type_name in ['restaurant', 'food', 'meal_delivery', 'meal_takeaway']:
                return 'Restaurant'
        
        return None

    def search_places_by_text(self, query: str, location: str = None) -> list:
        """
        Search for places using text query.
        
        Args:
            query: Text query (e.g., "pizza near Times Square")
            location: Optional location bias
            
        Returns:
            List of place results
        """
        if not self.client:
            logger.error("Google Places client not initialized")
            return []
        
        try:
            results = self.client.places(
                query=query,
                location=location,
                radius=5000  # 5km radius
            )
            
            return results.get('results', [])
            
        except Exception as e:
            logger.error(f"Error searching places: {str(e)}")
            return []

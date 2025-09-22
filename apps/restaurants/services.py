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

        api_key = getattr(settings, "GOOGLE_PLACES_API_KEY", None)
        if not api_key or not isinstance(api_key, str):
            if api_key:
                logger.warning(
                    "Google Places API key appears invalid; client disabled for safety"
                )
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
                "place_id",
                "name",
                "formatted_address",
                "geometry",
                "rating",
                "business_status",
                "type",
            ]

            result = self.client.place(place_id=place_id, fields=fields)

            if result.get("status") != "OK":
                logger.error(f"Google Places API error: {result.get('status')}")
                return None

            logger.info("--------------------------------")
            logger.info("RAW Result from Google Places API:")
            logger.info(result)
            logger.info("--------------------------------")

            place_data = result.get("result", {})

            # Extract geometry data
            geometry = place_data.get("geometry", {})
            location = geometry.get("location", {})

            # Extract cuisine types from Google Place types
            place_types = place_data.get("types") or []
            # Some APIs expose singular 'type'
            if not place_types and place_data.get("type"):
                place_types = [place_data.get("type")]
            cuisines = self._extract_cuisines_from_types(place_types)

            return {
                "place_id": place_data.get("place_id"),
                "name": place_data.get("name"),
                "address": place_data.get("formatted_address"),
                "latitude": (
                    float(location.get("lat", 0)) if location.get("lat") else None
                ),
                "longitude": (
                    float(location.get("lng", 0)) if location.get("lng") else None
                ),
                "rating": (
                    Decimal(str(place_data.get("rating", 0)))
                    if place_data.get("rating")
                    else None
                ),
                "cuisines": cuisines,
                "business_status": place_data.get("business_status", "UNKNOWN"),
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
                input_type="textquery",
                fields=["place_id", "name", "formatted_address", "geometry"],
            )
            candidates = (
                result.get("candidates", []) if isinstance(result, dict) else []
            )
            if not candidates:
                logger.info(f"No candidates found for text query: {text_query}")
                return None
            candidate = candidates[0]
            return {
                "place_id": candidate.get("place_id"),
                "name": candidate.get("name"),
                "formatted_address": candidate.get("formatted_address")
                or candidate.get("formatted_address"),
                "geometry": candidate.get("geometry"),
            }
        except Exception as e:
            logger.error(f"Error finding place from text '{text_query}': {str(e)}")
            return None

    def _extract_cuisines_from_types(self, types: list) -> list:
        """
        Extract cuisine types from Google Places types.

        Args:
            types: List of Google Place types

        Returns:
            List of cuisine type strings
        """
        # Official Google Places restaurant and food-related types
        food_related_types = {
            "acai_shop",
            "afghani_restaurant",
            "african_restaurant",
            "american_restaurant",
            "asian_restaurant",
            "bagel_shop",
            "bakery",
            "bar",
            "bar_and_grill",
            "barbecue_restaurant",
            "brazilian_restaurant",
            "breakfast_restaurant",
            "brunch_restaurant",
            "buffet_restaurant",
            "cafe",
            "cafeteria",
            "candy_store",
            "cat_cafe",
            "chinese_restaurant",
            "chocolate_factory",
            "chocolate_shop",
            "coffee_shop",
            "confectionery",
            "deli",
            "dessert_restaurant",
            "dessert_shop",
            "diner",
            "dog_cafe",
            "donut_shop",
            "fast_food_restaurant",
            "fine_dining_restaurant",
            "food_court",
            "french_restaurant",
            "greek_restaurant",
            "hamburger_restaurant",
            "ice_cream_shop",
            "indian_restaurant",
            "indonesian_restaurant",
            "italian_restaurant",
            "japanese_restaurant",
            "juice_shop",
            "korean_restaurant",
            "lebanese_restaurant",
            "meal_delivery",
            "meal_takeaway",
            "mediterranean_restaurant",
            "mexican_restaurant",
            "middle_eastern_restaurant",
            "pizza_restaurant",
            "pub",
            "ramen_restaurant",
            "restaurant",
            "sandwich_shop",
            "seafood_restaurant",
            "spanish_restaurant",
            "steak_house",
            "sushi_restaurant",
            "tea_house",
            "thai_restaurant",
            "turkish_restaurant",
            "vegan_restaurant",
            "vegetarian_restaurant",
            "vietnamese_restaurant",
            "wine_bar",
        }

        # Generic types to skip unless nothing else is found
        generic_types = {"restaurant", "meal_delivery", "meal_takeaway", "food"}

        cuisines = []

        # Look for specific food-related types first (excluding generic ones)
        for type_name in types:
            if type_name in food_related_types:
                # Convert type name to readable cuisine name
                cuisine_name = type_name.replace("_", " ").title()
                if cuisine_name not in cuisines:
                    cuisines.append(cuisine_name)

        # If no specific cuisines found, fall back to generic restaurant type
        if not cuisines:
            for type_name in types:
                if type_name in generic_types:
                    cuisines.append("Restaurant")
                    break

        return cuisines

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
                query=query, location=location, radius=5000  # 5km radius
            )

            return results.get("results", [])

        except Exception as e:
            logger.error(f"Error searching places: {str(e)}")
            return []

    def search_nearby_restaurants(
        self,
        latitude: float,
        longitude: float,
        radius: int = 2000,
        min_rating: float = None,
        max_price_level: int = None,
        cuisine_types: list = None,
        top_k_results: int = 20,
    ) -> list:
        """
        Search for restaurants near a given location with optional filters.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in meters (default 2km)
            min_rating: Minimum rating filter (e.g., 4.0 for good restaurants)
            max_price_level: Maximum price level (0=free, 1=inexpensive, 2=moderate, 3=expensive, 4=very expensive)
            cuisine_types: List of cuisine types to filter by
            top_k_results: Number of top results to return (default 20)
        Returns:
            List of restaurant results with details
        """
        if not self.client:
            logger.error("Google Places client not initialized")
            return []

        try:
            # Search for restaurants near the location
            results = self.client.places_nearby(
                location=(latitude, longitude), radius=radius, type="restaurant"
            )

            restaurants = []

            for place in results.get("results", []):
                # Apply rating filter
                if min_rating and place.get("rating", 0) < min_rating:
                    continue

                # Apply price level filter
                if (
                    max_price_level is not None
                    and place.get("price_level", 5) > max_price_level
                ):
                    continue

                # Apply cuisine type filter
                if cuisine_types:
                    place_types = place.get("types", [])
                    place_cuisines = self._extract_cuisines_from_types(place_types)

                    # Check if any of the place's cuisines match our desired cuisines
                    cuisine_match = False
                    for place_cuisine in place_cuisines:
                        for desired_cuisine in cuisine_types:
                            if desired_cuisine.lower() in place_cuisine.lower():
                                cuisine_match = True
                                break
                        if cuisine_match:
                            break

                    if not cuisine_match:
                        continue

                # Extract restaurant details
                restaurant_data = {
                    "place_id": place.get("place_id"),
                    "name": place.get("name"),
                    "rating": place.get("rating"),
                    "price_level": place.get("price_level"),
                    "vicinity": place.get("vicinity"),
                    "geometry": place.get("geometry"),
                    "types": place.get("types", []),
                    "cuisines": self._extract_cuisines_from_types(
                        place.get("types", [])
                    ),
                    "photos": place.get("photos", []),
                    "business_status": place.get("business_status", "OPERATIONAL"),
                }

                restaurants.append(restaurant_data)

            # Sort by rating descending by default
            restaurants.sort(key=lambda x: x.get("rating", 0), reverse=True)

            return restaurants[:top_k_results]  # Return top k results

        except Exception as e:
            logger.error(f"Error searching nearby restaurants: {str(e)}")
            return []

    def get_recommendations_near_location(
        self,
        latitude: float,
        longitude: float,
        recommendation_type: str,
        user_cuisines: list = None,
        radius: int = 2000,
        top_k_results: int = 20,
    ) -> list:
        """
        Get restaurant recommendations near a specific location.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            recommendation_type: Type of recommendation ('good', 'cheap', 'cuisine_match')
            user_cuisines: List of user's preferred cuisines (for cuisine_match type)

        Returns:
            List of recommended restaurants
        """
        if recommendation_type == "good":
            # Good restaurants: rating >= 4.0
            return self.search_nearby_restaurants(
                latitude=latitude,
                longitude=longitude,
                min_rating=4.0,
                radius=radius,
                top_k_results=top_k_results,
            )

        elif recommendation_type == "cheap":
            # Cheap restaurants: price level <= 1 (free or inexpensive)
            return self.search_nearby_restaurants(
                latitude=latitude,
                longitude=longitude,
                max_price_level=1,
                radius=radius,
                top_k_results=top_k_results,
            )

        elif recommendation_type == "cuisine_match" and user_cuisines:
            # Restaurants matching user's preferred cuisines
            return self.search_nearby_restaurants(
                latitude=latitude,
                longitude=longitude,
                cuisine_types=user_cuisines,
                radius=radius,
                top_k_results=top_k_results,
            )

        else:
            # Default: just return nearby restaurants
            return self.search_nearby_restaurants(
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                top_k_results=top_k_results,
            )

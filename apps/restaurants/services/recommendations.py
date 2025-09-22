"""
Restaurant recommendation service.
"""

import logging
from typing import List, Dict, Any
from apps.restaurants.models import UserRestaurantVisit, UserCuisineStat
from apps.restaurants.services import GooglePlacesService

logger = logging.getLogger(__name__)


class RestaurantRecommendationService:
    """Service for generating personalized restaurant recommendations."""

    def __init__(self):
        self.places_service = GooglePlacesService()

    def get_user_frequent_locations(self, user, limit: int = 5) -> List[Dict]:
        """
        Get user's most frequently visited restaurant locations.

        Args:
            user: User instance
            limit: Number of top locations to return

        Returns:
            List of location dictionaries with lat/lng coordinates
        """
        top_visits = (
            UserRestaurantVisit.objects.filter(
                user=user,
                restaurant__latitude__isnull=False,
                restaurant__longitude__isnull=False,
            )
            .select_related("restaurant")
            .order_by("-visit_count")[:limit]
        )

        locations = []
        for visit in top_visits:
            locations.append(
                {
                    "restaurant_name": visit.restaurant.name,
                    "latitude": visit.restaurant.latitude,
                    "longitude": visit.restaurant.longitude,
                    "visit_count": visit.visit_count,
                }
            )

        return locations

    def get_user_top_cuisines(self, user, limit: int = 5) -> List[str]:
        """
        Get user's most preferred cuisine types.

        Args:
            user: User instance
            limit: Number of top cuisines to return

        Returns:
            List of cuisine names
        """
        top_cuisines = (
            UserCuisineStat.objects.filter(user=user)
            .select_related("cuisine")
            .order_by("-visit_count")[:limit]
        )

        return [stat.cuisine.name for stat in top_cuisines]

    def get_good_restaurants_recommendations(
        self, user, limit: int = 20, radius: int = 2000, per_location_limit: int = 20
    ) -> List[Dict]:
        """
        Get highly-rated restaurant recommendations near user's frequent locations.

        Args:
            user: User instance
            limit: Maximum number of recommendations to return

        Returns:
            List of restaurant recommendation dictionaries
        """
        frequent_locations = self.get_user_frequent_locations(user)

        if not frequent_locations:
            logger.info(f"No frequent locations found for user {user.email}")
            return []

        all_recommendations = []

        for location in frequent_locations:
            try:
                recommendations = self.places_service.get_recommendations_near_location(
                    latitude=location["latitude"],
                    longitude=location["longitude"],
                    recommendation_type="good",
                    radius=radius,
                    top_k_results=per_location_limit,
                )

                # Add context about the reference location
                for rec in recommendations:
                    rec["reference_location"] = {
                        "restaurant_name": location["restaurant_name"],
                        "visit_count": location["visit_count"],
                    }
                    rec["recommendation_type"] = "good"

                all_recommendations.extend(recommendations)

            except Exception as e:
                logger.error(
                    f"Error getting good restaurant recommendations near {location['restaurant_name']}: {str(e)}"
                )
                continue

        # Remove duplicates and sort by rating
        unique_recommendations = self._deduplicate_recommendations(all_recommendations)
        unique_recommendations.sort(key=lambda x: x.get("rating", 0), reverse=True)

        return unique_recommendations[:limit]

    def get_cheap_restaurants_recommendations(
        self, user, limit: int = 20, radius: int = 2000, per_location_limit: int = 20
    ) -> List[Dict]:
        """
        Get budget-friendly restaurant recommendations near user's frequent locations.

        Args:
            user: User instance
            limit: Maximum number of recommendations to return

        Returns:
            List of restaurant recommendation dictionaries
        """
        frequent_locations = self.get_user_frequent_locations(user)

        if not frequent_locations:
            logger.info(f"No frequent locations found for user {user.email}")
            return []

        all_recommendations = []

        for location in frequent_locations:
            try:
                recommendations = self.places_service.get_recommendations_near_location(
                    latitude=location["latitude"],
                    longitude=location["longitude"],
                    recommendation_type="cheap",
                    radius=radius,
                    top_k_results=per_location_limit,
                )

                # Add context about the reference location
                for rec in recommendations:
                    rec["reference_location"] = {
                        "restaurant_name": location["restaurant_name"],
                        "visit_count": location["visit_count"],
                    }
                    rec["recommendation_type"] = "cheap"

                all_recommendations.extend(recommendations)

            except Exception as e:
                logger.error(
                    f"Error getting cheap restaurant recommendations near {location['restaurant_name']}: {str(e)}"
                )
                continue

        # Remove duplicates and sort by rating (even for cheap restaurants, prefer good ones)
        unique_recommendations = self._deduplicate_recommendations(all_recommendations)
        unique_recommendations.sort(key=lambda x: x.get("rating", 0), reverse=True)

        return unique_recommendations[:limit]

    def get_cuisine_match_recommendations(
        self, user, limit: int = 20, radius: int = 2000, per_location_limit: int = 20
    ) -> List[Dict]:
        """
        Get restaurant recommendations that match user's preferred cuisines near frequent locations.

        Args:
            user: User instance
            limit: Maximum number of recommendations to return

        Returns:
            List of restaurant recommendation dictionaries
        """
        frequent_locations = self.get_user_frequent_locations(user)
        user_cuisines = self.get_user_top_cuisines(user)

        if not frequent_locations:
            logger.info(f"No frequent locations found for user {user.email}")
            return []

        if not user_cuisines:
            logger.info(f"No cuisine preferences found for user {user.email}")
            return []

        all_recommendations = []

        for location in frequent_locations:
            try:
                recommendations = self.places_service.get_recommendations_near_location(
                    latitude=location["latitude"],
                    longitude=location["longitude"],
                    recommendation_type="cuisine_match",
                    user_cuisines=user_cuisines,
                    radius=radius,
                    top_k_results=per_location_limit,
                )

                # Add context about the reference location and matched cuisines
                for rec in recommendations:
                    rec["reference_location"] = {
                        "restaurant_name": location["restaurant_name"],
                        "visit_count": location["visit_count"],
                    }
                    rec["recommendation_type"] = "cuisine_match"
                    rec["matched_cuisines"] = self._get_matching_cuisines(
                        rec.get("cuisines", []), user_cuisines
                    )

                all_recommendations.extend(recommendations)

            except Exception as e:
                logger.error(
                    f"Error getting cuisine-based recommendations near {location['restaurant_name']}: {str(e)}"
                )
                continue

        # Remove duplicates and sort by rating
        unique_recommendations = self._deduplicate_recommendations(all_recommendations)
        unique_recommendations.sort(key=lambda x: x.get("rating", 0), reverse=True)

        return unique_recommendations[:limit]

    def _deduplicate_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """
        Remove duplicate restaurants from recommendations list.

        Args:
            recommendations: List of restaurant dictionaries

        Returns:
            List of unique restaurant dictionaries
        """
        seen_place_ids = set()
        unique_recommendations = []

        for rec in recommendations:
            place_id = rec.get("place_id")
            if place_id and place_id not in seen_place_ids:
                seen_place_ids.add(place_id)
                unique_recommendations.append(rec)

        return unique_recommendations

    def _get_matching_cuisines(
        self, restaurant_cuisines: List[str], user_cuisines: List[str]
    ) -> List[str]:
        """
        Get the cuisines that match between restaurant and user preferences.

        Args:
            restaurant_cuisines: List of restaurant's cuisines
            user_cuisines: List of user's preferred cuisines

        Returns:
            List of matching cuisine names
        """
        matching = []

        for restaurant_cuisine in restaurant_cuisines:
            for user_cuisine in user_cuisines:
                if user_cuisine.lower() in restaurant_cuisine.lower():
                    matching.append(restaurant_cuisine)
                    break

        return matching

    def get_all_recommendations(
        self,
        user,
        limit_per_type: int = 10,
        radius: int = 2000,
        per_location_limit: int = 20,
    ) -> Dict[str, List[Dict]]:
        """
        Get all three types of recommendations for a user.

        Args:
            user: User instance
            limit_per_type: Maximum number of recommendations per type

        Returns:
            Dictionary with keys 'good', 'cheap', 'cuisine_match' containing recommendation lists
        """
        return {
            "good": self.get_good_restaurants_recommendations(
                user, limit_per_type, radius, per_location_limit
            ),
            "cheap": self.get_cheap_restaurants_recommendations(
                user, limit_per_type, radius, per_location_limit
            ),
            "cuisine_match": self.get_cuisine_match_recommendations(
                user, limit_per_type, radius, per_location_limit
            ),
        }

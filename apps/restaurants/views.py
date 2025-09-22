from rest_framework import filters, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Restaurant
from .serializers import (
    RestaurantSerializer,
    RestaurantListSerializer,
    RestaurantDetailSerializer,
    RecommendationResponseSerializer,
    AllRecommendationsSerializer,
)
from .services.recommendations import RestaurantRecommendationService
from .services.visit_tracking import get_user_top_restaurants, get_user_top_cuisines


class RestaurantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Restaurant objects.
    Provides CRUD operations with filtering and search capabilities.
    """

    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    permission_classes = [IsAuthenticated]

    # Enable filtering and search
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    # Fields that can be searched
    search_fields = ["name", "address", "cuisines__name"]

    # Fields that can be used for ordering
    ordering_fields = ["name", "rating", "updated_at"]
    ordering = ["name"]  # Default ordering

    def get_queryset(self):
        """
        Optionally restricts the returned restaurants by filtering against
        query parameters in the URL.
        """
        queryset = Restaurant.objects.all()

        # Filter by cuisine
        cuisine = self.request.query_params.get("cuisine")
        if cuisine is not None:
            queryset = queryset.filter(cuisines__name__icontains=cuisine)

        # Filter by name
        name = self.request.query_params.get("name")
        if name is not None:
            queryset = queryset.filter(name__icontains=name)

        # Filter by rating range
        rating_min = self.request.query_params.get("rating_min")
        rating_max = self.request.query_params.get("rating_max")

        if rating_min is not None:
            try:
                queryset = queryset.filter(rating__gte=float(rating_min))
            except ValueError:
                pass

        if rating_max is not None:
            try:
                queryset = queryset.filter(rating__lte=float(rating_max))
            except ValueError:
                pass

        return queryset

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        """
        if self.action == "list":
            return RestaurantListSerializer
        elif self.action in ["retrieve"]:
            return RestaurantDetailSerializer
        return RestaurantSerializer

    @swagger_auto_schema(
        method="get",
        operation_summary="Highly-rated recommendations",
        operation_description="Return highly-rated restaurants near the user's frequent locations.",
        manual_parameters=[
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Max results to return (default 20)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                "radius",
                openapi.IN_QUERY,
                description="Search radius in meters (default 2000)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                "search_limit",
                openapi.IN_QUERY,
                description="Per-location upstream search limit (default 20)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                description="List of highly-rated recommendations",
                examples={
                    "application/json": {
                        "recommendation_type": "good",
                        "count": 2,
                        "recommendations": [
                            {
                                "place_id": "ChIJ-good-japanese-3",
                                "name": "Sakura Sushi",
                                "rating": 4.8,
                                "price_level": 2,
                                "price_description": "Moderate",
                                "vicinity": "789 Cherry Blossom Rd, Springfield, USA",
                                "formatted_address": "789 Cherry Blossom Rd, Springfield, USA",
                                "cuisines": ["Japanese"],
                                "recommendation_type": "good",
                                "business_status": "OPERATIONAL",
                                "geometry": {
                                    "location": {"lat": 40.7128, "lng": -74.006}
                                },
                                "latitude": 40.7128,
                                "longitude": -74.006,
                                "reference_location": {
                                    "name": "Home Area",
                                    "latitude": 40.713,
                                    "longitude": -74.01,
                                },
                            },
                            {
                                "place_id": "ChIJ-good-mediterranean-5",
                                "name": "Aegean Breeze",
                                "rating": 4.7,
                                "price_level": 2,
                                "price_description": "Moderate",
                                "vicinity": "654 Olive Grove Ln, Springfield, USA",
                                "formatted_address": "654 Olive Grove Ln, Springfield, USA",
                                "cuisines": ["Mediterranean"],
                                "recommendation_type": "good",
                                "business_status": "OPERATIONAL",
                                "geometry": {
                                    "location": {"lat": 41.8781, "lng": -87.6298}
                                },
                                "latitude": 41.8781,
                                "longitude": -87.6298,
                                "reference_location": {
                                    "name": "Work Area",
                                    "latitude": 41.88,
                                    "longitude": -87.63,
                                },
                            },
                        ],
                        "user_context": {
                            "frequent_restaurants": [
                                {"name": "Trattoria Roma", "visit_count": 12},
                                {"name": "Sakura Sushi", "visit_count": 10},
                            ]
                        },
                    }
                },
            ),
            500: openapi.Response(description="Failed to get recommendations"),
        },
        tags=["Recommendations"],
    )
    @action(detail=False, methods=["get"], url_path="recommendations/good")
    def good_recommendations(self, request):
        """Get highly-rated restaurant recommendations near user's frequent locations."""
        try:
            recommendation_service = RestaurantRecommendationService()
            radius = int(request.query_params.get("radius", 2000))
            per_location_limit = int(request.query_params.get("search_limit", 20))
            recommendations = (
                recommendation_service.get_good_restaurants_recommendations(
                    user=request.user,
                    limit=int(request.query_params.get("limit", 20)),
                    radius=radius,
                    per_location_limit=per_location_limit,
                )
            )

            # Get user context
            top_restaurants = get_user_top_restaurants(request.user, limit=5)
            user_context = {
                "frequent_restaurants": [
                    {"name": restaurant.name, "visit_count": visit_count}
                    for restaurant, visit_count in top_restaurants
                ]
            }

            response_data = {
                "recommendation_type": "good",
                "count": len(recommendations),
                "recommendations": recommendations,
                "user_context": user_context,
            }

            serializer = RecommendationResponseSerializer(response_data)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"error": f"Failed to get recommendations: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        method="get",
        operation_summary="Budget-friendly recommendations",
        operation_description="Return budget-friendly restaurants near the user's frequent locations.",
        manual_parameters=[
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Max results to return (default 20)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                "radius",
                openapi.IN_QUERY,
                description="Search radius in meters (default 2000)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                "search_limit",
                openapi.IN_QUERY,
                description="Per-location upstream search limit (default 20)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                description="List of budget-friendly recommendations",
                examples={
                    "application/json": {
                        "recommendation_type": "cheap",
                        "count": 2,
                        "recommendations": [
                            {
                                "place_id": "ChIJ-cheap-mexican-2",
                                "name": "Taqueria El Sol",
                                "rating": 4.2,
                                "price_level": 1,
                                "price_description": "Inexpensive",
                                "vicinity": "456 Fiesta Ave, Springfield, USA",
                                "formatted_address": "456 Fiesta Ave, Springfield, USA",
                                "cuisines": ["Mexican"],
                                "recommendation_type": "cheap",
                                "business_status": "OPERATIONAL",
                                "geometry": {
                                    "location": {"lat": 34.0522, "lng": -118.2437}
                                },
                                "latitude": 34.0522,
                                "longitude": -118.2437,
                                "reference_location": {
                                    "name": "Home Area",
                                    "latitude": 34.05,
                                    "longitude": -118.24,
                                },
                            }
                        ],
                        "user_context": {
                            "frequent_restaurants": [
                                {"name": "Taqueria El Sol", "visit_count": 9}
                            ]
                        },
                    }
                },
            ),
            500: openapi.Response(description="Failed to get recommendations"),
        },
        tags=["Recommendations"],
    )
    @action(detail=False, methods=["get"], url_path="recommendations/cheap")
    def cheap_recommendations(self, request):
        """Get budget-friendly restaurant recommendations near user's frequent locations."""
        try:
            recommendation_service = RestaurantRecommendationService()
            radius = int(request.query_params.get("radius", 2000))
            per_location_limit = int(request.query_params.get("search_limit", 20))
            recommendations = (
                recommendation_service.get_cheap_restaurants_recommendations(
                    user=request.user,
                    limit=int(request.query_params.get("limit", 20)),
                    radius=radius,
                    per_location_limit=per_location_limit,
                )
            )

            # Get user context
            top_restaurants = get_user_top_restaurants(request.user, limit=5)
            user_context = {
                "frequent_restaurants": [
                    {"name": restaurant.name, "visit_count": visit_count}
                    for restaurant, visit_count in top_restaurants
                ]
            }

            response_data = {
                "recommendation_type": "cheap",
                "count": len(recommendations),
                "recommendations": recommendations,
                "user_context": user_context,
            }

            serializer = RecommendationResponseSerializer(response_data)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"error": f"Failed to get recommendations: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        method="get",
        operation_summary="Cuisine match recommendations",
        operation_description="Return restaurants that match the user's preferred cuisines near frequent locations.",
        manual_parameters=[
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Max results to return (default 20)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                "radius",
                openapi.IN_QUERY,
                description="Search radius in meters (default 2000)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                "search_limit",
                openapi.IN_QUERY,
                description="Per-location upstream search limit (default 20)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                description="List of cuisine-matched recommendations",
                examples={
                    "application/json": {
                        "recommendation_type": "cuisine_match",
                        "count": 2,
                        "recommendations": [
                            {
                                "place_id": "ChIJ-cuisine-match-4",
                                "name": "Bombay Spice",
                                "rating": 4.5,
                                "price_level": 2,
                                "price_description": "Moderate",
                                "vicinity": "321 Masala St, Springfield, USA",
                                "formatted_address": "321 Masala St, Springfield, USA",
                                "cuisines": ["Indian"],
                                "matched_cuisines": ["Indian"],
                                "recommendation_type": "cuisine_match",
                                "business_status": "OPERATIONAL",
                                "geometry": {
                                    "location": {"lat": 47.6062, "lng": -122.3321}
                                },
                                "latitude": 47.6062,
                                "longitude": -122.3321,
                            }
                        ],
                        "user_context": {
                            "frequent_restaurants": [
                                {"name": "Sakura Sushi", "visit_count": 10}
                            ],
                            "preferred_cuisines": [
                                {"name": "Japanese", "visit_count": 20},
                                {"name": "Mediterranean", "visit_count": 14},
                            ],
                        },
                    }
                },
            ),
            500: openapi.Response(description="Failed to get recommendations"),
        },
        tags=["Recommendations"],
    )
    @action(detail=False, methods=["get"], url_path="recommendations/cuisine-match")
    def cuisine_match_recommendations(self, request):
        """Get restaurant recommendations matching user's preferred cuisines near frequent locations."""
        try:
            recommendation_service = RestaurantRecommendationService()
            radius = int(request.query_params.get("radius", 2000))
            per_location_limit = int(request.query_params.get("search_limit", 20))
            recommendations = recommendation_service.get_cuisine_match_recommendations(
                user=request.user,
                limit=int(request.query_params.get("limit", 20)),
                radius=radius,
                per_location_limit=per_location_limit,
            )

            # Get user context
            top_restaurants = get_user_top_restaurants(request.user, limit=5)
            top_cuisines = get_user_top_cuisines(request.user, limit=5)
            user_context = {
                "frequent_restaurants": [
                    {"name": restaurant.name, "visit_count": visit_count}
                    for restaurant, visit_count in top_restaurants
                ],
                "preferred_cuisines": [
                    {"name": cuisine.name, "visit_count": visit_count}
                    for cuisine, visit_count in top_cuisines
                ],
            }

            response_data = {
                "recommendation_type": "cuisine_match",
                "count": len(recommendations),
                "recommendations": recommendations,
                "user_context": user_context,
            }

            serializer = RecommendationResponseSerializer(response_data)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"error": f"Failed to get recommendations: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        method="get",
        operation_summary="All recommendation types",
        operation_description="Return all three categories of recommendations in a single response.",
        manual_parameters=[
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Max results per type (default 10)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                "radius",
                openapi.IN_QUERY,
                description="Search radius in meters (default 2000)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                "search_limit",
                openapi.IN_QUERY,
                description="Per-location upstream search limit (default 20)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Aggregated recommendations",
                examples={
                    "application/json": {
                        "good": [
                            {
                                "place_id": "ChIJ-good-japanese-3",
                                "name": "Sakura Sushi",
                                "rating": 4.8,
                                "price_level": 2,
                                "price_description": "Moderate",
                                "vicinity": "789 Cherry Blossom Rd, Springfield, USA",
                                "formatted_address": "789 Cherry Blossom Rd, Springfield, USA",
                                "cuisines": ["Japanese"],
                                "recommendation_type": "good",
                                "business_status": "OPERATIONAL",
                            }
                        ],
                        "cheap": [
                            {
                                "place_id": "ChIJ-cheap-mexican-2",
                                "name": "Taqueria El Sol",
                                "rating": 4.2,
                                "price_level": 1,
                                "price_description": "Inexpensive",
                                "vicinity": "456 Fiesta Ave, Springfield, USA",
                                "formatted_address": "456 Fiesta Ave, Springfield, USA",
                                "cuisines": ["Mexican"],
                                "recommendation_type": "cheap",
                                "business_status": "OPERATIONAL",
                            }
                        ],
                        "cuisine_match": [
                            {
                                "place_id": "ChIJ-cuisine-match-4",
                                "name": "Bombay Spice",
                                "rating": 4.5,
                                "price_level": 2,
                                "price_description": "Moderate",
                                "vicinity": "321 Masala St, Springfield, USA",
                                "formatted_address": "321 Masala St, Springfield, USA",
                                "cuisines": ["Indian"],
                                "matched_cuisines": ["Indian"],
                                "recommendation_type": "cuisine_match",
                                "business_status": "OPERATIONAL",
                            }
                        ],
                        "user_context": {
                            "frequent_restaurants": [
                                {"name": "Trattoria Roma", "visit_count": 12},
                                {"name": "Sakura Sushi", "visit_count": 10},
                            ],
                            "preferred_cuisines": [
                                {"name": "Japanese", "visit_count": 20},
                                {"name": "Mediterranean", "visit_count": 14},
                            ],
                        },
                    }
                },
            ),
            500: openapi.Response(description="Failed to get recommendations"),
        },
        tags=["Recommendations"],
    )
    @action(detail=False, methods=["get"], url_path="recommendations/all")
    def all_recommendations(self, request):
        """Get all three types of restaurant recommendations."""
        try:
            recommendation_service = RestaurantRecommendationService()
            limit_per_type = int(request.query_params.get("limit", 10))
            radius = int(request.query_params.get("radius", 2000))
            per_location_limit = int(request.query_params.get("search_limit", 20))

            all_recommendations = recommendation_service.get_all_recommendations(
                user=request.user,
                limit_per_type=limit_per_type,
                radius=radius,
                per_location_limit=per_location_limit,
            )

            # Get user context
            top_restaurants = get_user_top_restaurants(request.user, limit=5)
            top_cuisines = get_user_top_cuisines(request.user, limit=5)
            user_context = {
                "frequent_restaurants": [
                    {"name": restaurant.name, "visit_count": visit_count}
                    for restaurant, visit_count in top_restaurants
                ],
                "preferred_cuisines": [
                    {"name": cuisine.name, "visit_count": visit_count}
                    for cuisine, visit_count in top_cuisines
                ],
            }

            response_data = {**all_recommendations, "user_context": user_context}

            serializer = AllRecommendationsSerializer(response_data)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"error": f"Failed to get recommendations: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

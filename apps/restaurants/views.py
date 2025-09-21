from rest_framework import filters, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Restaurant
from .serializers import (
    RestaurantSerializer,
    RestaurantListSerializer,
    RestaurantDetailSerializer,
    RecommendationResponseSerializer,
    AllRecommendationsSerializer
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
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    
    # Fields that can be searched
    search_fields = ['name', 'address', 'cuisines__name']
    
    # Fields that can be used for ordering
    ordering_fields = ['name', 'rating', 'updated_at']
    ordering = ['name']  # Default ordering
    
    def get_queryset(self):
        """
        Optionally restricts the returned restaurants by filtering against
        query parameters in the URL.
        """
        queryset = Restaurant.objects.all()
        
        # Filter by cuisine
        cuisine = self.request.query_params.get('cuisine')
        if cuisine is not None:
            queryset = queryset.filter(cuisines__name__icontains=cuisine)
        
        # Filter by name
        name = self.request.query_params.get('name')
        if name is not None:
            queryset = queryset.filter(name__icontains=name)
        
        # Filter by rating range
        rating_min = self.request.query_params.get('rating_min')
        rating_max = self.request.query_params.get('rating_max')
        
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
        if self.action == 'list':
            return RestaurantListSerializer
        elif self.action in ['retrieve']:
            return RestaurantDetailSerializer
        return RestaurantSerializer
    
    @action(detail=False, methods=['get'], url_path='recommendations/good')
    def good_recommendations(self, request):
        """Get highly-rated restaurant recommendations near user's frequent locations."""
        try:
            recommendation_service = RestaurantRecommendationService()
            radius = int(request.query_params.get('radius', 2000))
            per_location_limit = int(request.query_params.get('search_limit', 20))
            recommendations = recommendation_service.get_good_restaurants_recommendations(
                user=request.user,
                limit=int(request.query_params.get('limit', 20)),
                radius=radius,
                per_location_limit=per_location_limit
            )
            
            # Get user context
            top_restaurants = get_user_top_restaurants(request.user, limit=5)
            user_context = {
                'frequent_restaurants': [
                    {'name': restaurant.name, 'visit_count': visit_count} 
                    for restaurant, visit_count in top_restaurants
                ]
            }
            
            response_data = {
                'recommendation_type': 'good',
                'count': len(recommendations),
                'recommendations': recommendations,
                'user_context': user_context
            }
            
            serializer = RecommendationResponseSerializer(response_data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get recommendations: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='recommendations/cheap')
    def cheap_recommendations(self, request):
        """Get budget-friendly restaurant recommendations near user's frequent locations."""
        try:
            recommendation_service = RestaurantRecommendationService()
            radius = int(request.query_params.get('radius', 2000))
            per_location_limit = int(request.query_params.get('search_limit', 20))
            recommendations = recommendation_service.get_cheap_restaurants_recommendations(
                user=request.user,
                limit=int(request.query_params.get('limit', 20)),
                radius=radius,
                per_location_limit=per_location_limit
            )
            
            # Get user context
            top_restaurants = get_user_top_restaurants(request.user, limit=5)
            user_context = {
                'frequent_restaurants': [
                    {'name': restaurant.name, 'visit_count': visit_count} 
                    for restaurant, visit_count in top_restaurants
                ]
            }
            
            response_data = {
                'recommendation_type': 'cheap',
                'count': len(recommendations),
                'recommendations': recommendations,
                'user_context': user_context
            }
            
            serializer = RecommendationResponseSerializer(response_data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get recommendations: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='recommendations/cuisine-match')
    def cuisine_match_recommendations(self, request):
        """Get restaurant recommendations matching user's preferred cuisines near frequent locations."""
        try:
            recommendation_service = RestaurantRecommendationService()
            radius = int(request.query_params.get('radius', 2000))
            per_location_limit = int(request.query_params.get('search_limit', 20))
            recommendations = recommendation_service.get_cuisine_match_recommendations(
                user=request.user,
                limit=int(request.query_params.get('limit', 20)),
                radius=radius,
                per_location_limit=per_location_limit
            )
            
            # Get user context
            top_restaurants = get_user_top_restaurants(request.user, limit=5)
            top_cuisines = get_user_top_cuisines(request.user, limit=5)
            user_context = {
                'frequent_restaurants': [
                    {'name': restaurant.name, 'visit_count': visit_count} 
                    for restaurant, visit_count in top_restaurants
                ],
                'preferred_cuisines': [
                    {'name': cuisine.name, 'visit_count': visit_count} 
                    for cuisine, visit_count in top_cuisines
                ]
            }
            
            response_data = {
                'recommendation_type': 'cuisine_match',
                'count': len(recommendations),
                'recommendations': recommendations,
                'user_context': user_context
            }
            
            serializer = RecommendationResponseSerializer(response_data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get recommendations: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='recommendations/all')
    def all_recommendations(self, request):
        """Get all three types of restaurant recommendations."""
        try:
            recommendation_service = RestaurantRecommendationService()
            limit_per_type = int(request.query_params.get('limit', 10))
            radius = int(request.query_params.get('radius', 2000))
            per_location_limit = int(request.query_params.get('search_limit', 20))
            
            all_recommendations = recommendation_service.get_all_recommendations(
                user=request.user,
                limit_per_type=limit_per_type,
                radius=radius,
                per_location_limit=per_location_limit
            )
            
            # Get user context
            top_restaurants = get_user_top_restaurants(request.user, limit=5)
            top_cuisines = get_user_top_cuisines(request.user, limit=5)
            user_context = {
                'frequent_restaurants': [
                    {'name': restaurant.name, 'visit_count': visit_count} 
                    for restaurant, visit_count in top_restaurants
                ],
                'preferred_cuisines': [
                    {'name': cuisine.name, 'visit_count': visit_count} 
                    for cuisine, visit_count in top_cuisines
                ]
            }
            
            response_data = {
                **all_recommendations,
                'user_context': user_context
            }
            
            serializer = AllRecommendationsSerializer(response_data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get recommendations: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

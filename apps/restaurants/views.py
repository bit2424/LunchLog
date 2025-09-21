from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Restaurant
from .serializers import (
    RestaurantSerializer,
    RestaurantListSerializer,
    RestaurantDetailSerializer
)


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

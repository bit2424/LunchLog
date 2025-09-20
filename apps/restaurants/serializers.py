from rest_framework import serializers
from .models import Restaurant


class RestaurantSerializer(serializers.ModelSerializer):
    """Serializer for Restaurant model."""
    
    class Meta:
        model = Restaurant
        fields = [
            'id',
            'place_id',
            'name',
            'address',
            'latitude',
            'longitude',
            'cuisine',
            'rating',
            'updated_at'
        ]
        read_only_fields = ['id', 'place_id', 'updated_at']
    
    def validate_latitude(self, value):
        """Validate latitude is within valid range."""
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90 degrees.")
        return value
    
    def validate_longitude(self, value):
        """Validate longitude is within valid range."""
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180 degrees.")
        return value
    
    def validate_rating(self, value):
        """Validate rating is within reasonable range."""
        if value is not None and not 0 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 0 and 5.")
        return value


class RestaurantListSerializer(RestaurantSerializer):
    """Simplified serializer for listing restaurants."""
    
    class Meta(RestaurantSerializer.Meta):
        fields = [
            'id',
            'place_id',
            'name',
            'address',
            'cuisine',
            'rating'
        ]


class RestaurantDetailSerializer(RestaurantSerializer):
    """Detailed serializer with all fields for restaurant details."""
    pass  # Uses all fields from parent RestaurantSerializer

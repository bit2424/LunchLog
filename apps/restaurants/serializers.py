from rest_framework import serializers
from .models import Restaurant, Cuisine


class CuisineSerializer(serializers.ModelSerializer):
    """Serializer for Cuisine model."""
    
    class Meta:
        model = Cuisine
        fields = ['id', 'name']


class RestaurantSerializer(serializers.ModelSerializer):
    """Serializer for Restaurant model."""
    
    cuisines = CuisineSerializer(many=True, read_only=True)
    cuisine_names = serializers.ListField(
        child=serializers.CharField(max_length=200),
        write_only=True,
        required=False,
        help_text="List of cuisine names"
    )
    
    class Meta:
        model = Restaurant
        fields = [
            'id',
            'place_id',
            'name',
            'address',
            'latitude',
            'longitude',
            'cuisines',
            'cuisine_names',
            'rating',
            'updated_at'
        ]
        read_only_fields = ['id', 'place_id', 'updated_at']
    
    def create(self, validated_data):
        """Create restaurant with cuisines."""
        cuisine_names = validated_data.pop('cuisine_names', [])
        restaurant = Restaurant.objects.create(**validated_data)
        
        # Handle cuisines
        if cuisine_names:
            cuisine_objects = []
            for cuisine_name in cuisine_names:
                cuisine, created = Cuisine.objects.get_or_create(name=cuisine_name)
                cuisine_objects.append(cuisine)
            restaurant.cuisines.set(cuisine_objects)
        
        return restaurant
    
    def update(self, instance, validated_data):
        """Update restaurant with cuisines."""
        cuisine_names = validated_data.pop('cuisine_names', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle cuisines if provided
        if cuisine_names is not None:
            cuisine_objects = []
            for cuisine_name in cuisine_names:
                cuisine, created = Cuisine.objects.get_or_create(name=cuisine_name)
                cuisine_objects.append(cuisine)
            instance.cuisines.set(cuisine_objects)
        
        return instance
    
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
            'cuisines',
            'rating'
        ]


class RestaurantDetailSerializer(RestaurantSerializer):
    """Detailed serializer with all fields for restaurant details."""
    pass  # Uses all fields from parent RestaurantSerializer

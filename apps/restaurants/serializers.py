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


class RecommendationSerializer(serializers.Serializer):
    """Serializer for restaurant recommendations from Google Places."""
    
    place_id = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255)
    rating = serializers.FloatField(required=False, allow_null=True)
    price_level = serializers.IntegerField(required=False, allow_null=True)
    vicinity = serializers.CharField(max_length=500, required=False, allow_null=True)
    cuisines = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    recommendation_type = serializers.CharField(max_length=50)
    business_status = serializers.CharField(max_length=50, default='OPERATIONAL')
    
    # Reference location info
    reference_location = serializers.DictField(required=False)
    
    # Additional fields for cuisine match recommendations
    matched_cuisines = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    
    # Geometry information
    geometry = serializers.DictField(required=False)
    
    def to_representation(self, instance):
        """Custom representation to format the data nicely."""
        data = super().to_representation(instance)
        
        # Add formatted address from vicinity
        if data.get('vicinity'):
            data['formatted_address'] = data['vicinity']
        
        # Add location coordinates if geometry is available
        geometry = data.get('geometry', {})
        location = geometry.get('location', {})
        if location:
            data['latitude'] = location.get('lat')
            data['longitude'] = location.get('lng')
        
        # Format price level description
        price_level = data.get('price_level')
        if price_level is not None:
            price_descriptions = {
                0: 'Free',
                1: 'Inexpensive',
                2: 'Moderate',
                3: 'Expensive',
                4: 'Very Expensive'
            }
            data['price_description'] = price_descriptions.get(price_level, 'Unknown')
        
        return data


class RecommendationResponseSerializer(serializers.Serializer):
    """Serializer for recommendation API responses."""
    
    recommendation_type = serializers.CharField(max_length=50)
    count = serializers.IntegerField()
    recommendations = RecommendationSerializer(many=True)
    user_context = serializers.DictField(required=False)


class AllRecommendationsSerializer(serializers.Serializer):
    """Serializer for all recommendation types response."""
    
    good = RecommendationSerializer(many=True)
    cheap = RecommendationSerializer(many=True)
    cuisine_match = RecommendationSerializer(many=True)
    user_context = serializers.DictField(required=False)

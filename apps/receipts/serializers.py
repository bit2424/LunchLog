from PIL import Image
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Receipt
from apps.restaurants.serializers import RestaurantSerializer
from apps.restaurants.models import Restaurant

User = get_user_model()


class ReceiptSerializer(serializers.ModelSerializer):
    """Serializer for Receipt model with image upload handling."""
    
    image_url = serializers.SerializerMethodField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    restaurant = RestaurantSerializer(read_only=True)
    restaurant_id = serializers.IntegerField(
        source='restaurant.id',
        write_only=True,
        allow_null=True,
        required=False
    )
    
    class Meta:
        model = Receipt
        fields = [
            'id',
            'user',
            'date',
            'price',
            'restaurant',
            'restaurant_id',
            'restaurant_name',
            'address',
            'image',
            'image_url',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'restaurant', 'image_url', 'created_at', 'updated_at']
    
    def validate_restaurant_id(self, value):
        """Validate that the restaurant exists."""
        if value is not None:
            if not Restaurant.objects.filter(id=value).exists():
                raise serializers.ValidationError("Restaurant with this ID does not exist.")
        return value
    
    def get_image_url(self, obj):
        """Return the URL of the receipt image."""
        return obj.image_url
    
    def create(self, validated_data):
        """Create a new receipt with the current user."""
        # Get the user from the request context
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Handle restaurant_id field
        restaurant_data = validated_data.pop('restaurant', {})
        restaurant_id = restaurant_data.get('id')
        if restaurant_id:
            from apps.restaurants.models import Restaurant
            validated_data['restaurant'] = Restaurant.objects.get(id=restaurant_id)
        
        return super().create(validated_data)
    
    def to_representation(self, instance):
        """Return canonicalized payload with image_url."""
        data = super().to_representation(instance)
        
        # Ensure we return the image_url instead of the image field for API responses
        if 'image' in data and instance.image:
            data['image_url'] = instance.image.url
            # Remove the image field from the response to keep it clean
            data.pop('image', None)
        
        return data


class ReceiptCreateSerializer(ReceiptSerializer):
    """Specialized serializer for creating receipts with proper validation."""
    
    class Meta(ReceiptSerializer.Meta):
        fields = [
            'id',
            'date',
            'price',
            'restaurant_id',
            'restaurant_name',
            'address',
            'image',
            'image_url',
            'created_at',
            'updated_at'
        ]
        
    def validate_image(self, value):
        """Validate the uploaded image file (size + type)."""
        if not value:
            raise serializers.ValidationError("Image file is required.")

        # Size check (1MB max)
        max_size = 1 * 1024 * 1024
        if int(value.size) > max_size:
            raise serializers.ValidationError(
                f"Image file too large MB). "
                "Maximum size allowed is 10 MB."
            )

        # File format check using Pillow
        try:
            img = Image.open(value)
            img.verify()
        except Exception:
            raise serializers.ValidationError("Uploaded file is not a valid image.")

        allowed_formats = ["JPEG", "PNG", "GIF"]
        if img.format not in allowed_formats:
            raise serializers.ValidationError(
                f"Unsupported image format: {img.format}. "
                f"Allowed formats are: {', '.join(allowed_formats)}."
            )

        return value


class ReceiptListSerializer(ReceiptSerializer):
    """Simplified serializer for listing receipts."""
    
    class Meta(ReceiptSerializer.Meta):
        fields = [
            'id',
            'date',
            'price',
            'restaurant',
            'restaurant_name', 
            'address',  
            'image_url',
            'created_at'
        ]

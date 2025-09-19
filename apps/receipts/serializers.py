from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Receipt

User = get_user_model()


class ReceiptSerializer(serializers.ModelSerializer):
    """Serializer for Receipt model with image upload handling."""
    
    image_url = serializers.SerializerMethodField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Receipt
        fields = [
            'id',
            'user',
            'date',
            'price',
            'restaurant_name',
            'address',
            'image',
            'image_url',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'image_url', 'created_at', 'updated_at']
    
    def get_image_url(self, obj):
        """Return the URL of the receipt image."""
        return obj.image_url
    
    def create(self, validated_data):
        """Create a new receipt with the current user."""
        # Get the user from the request context
        user = self.context['request'].user
        validated_data['user'] = user
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
            'restaurant_name',
            'address',
            'image',
            'image_url',
            'created_at',
            'updated_at'
        ]
        
    def validate_image(self, value):
        """Validate the uploaded image file."""
        if not value:
            raise serializers.ValidationError("Image file is required.")
        
        # Check file size (limit to 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Image file too large. Size should not exceed 10MB.")
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
        if hasattr(value, 'content_type') and value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Unsupported file type. Please upload a JPEG, PNG, or GIF image."
            )
        
        return value


class ReceiptListSerializer(ReceiptSerializer):
    """Simplified serializer for listing receipts."""
    
    class Meta(ReceiptSerializer.Meta):
        fields = [
            'id',
            'date',
            'price',
            'restaurant_name',
            'address',
            'image_url',
            'created_at'
        ]

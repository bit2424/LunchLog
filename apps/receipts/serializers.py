from PIL import Image
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
            'restaurant_name',
            'address',
            'image_url',
            'created_at'
        ]

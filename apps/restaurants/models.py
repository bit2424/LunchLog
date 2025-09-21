import uuid
from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator


class Cuisine(models.Model):
    """Model representing a cuisine type."""
    
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Cuisine type name (e.g., Italian, Chinese, American)"
    )
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Restaurant(models.Model):
    """Model representing a restaurant with Google Places integration."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    place_id = models.CharField(
        max_length=255, 
        unique=True,
        help_text="Google Places API place_id"
    )
    name = models.CharField(
        max_length=255,
        help_text="Restaurant name"
    )
    address = models.TextField(
        help_text="Full formatted address"
    )
    latitude = models.FloatField(
        blank=True,
        null=True,
        help_text="Latitude coordinate"
    )
    longitude = models.FloatField(
        blank=True,
        null=True,
        help_text="Longitude coordinate"
    )
    cuisines = models.ManyToManyField(
        Cuisine, 
        related_name="restaurants",
        blank=True,
        help_text="Cuisine types associated with this restaurant"
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True, 
        null=True,
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('5.00'))
        ],
        help_text="Average rating from Google Places (0.00-5.00)"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last updated timestamp"
    )

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['place_id'], name='restaurant_place_id_idx'),
            models.Index(fields=['name'], name='restaurant_name_idx'),
        ]

    def __str__(self):
        return self.name

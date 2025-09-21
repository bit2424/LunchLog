import uuid
from django.db import models
from django.conf import settings
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


class UserRestaurantVisit(models.Model):
    """Model tracking how many times a user has visited each restaurant."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='restaurant_visits'
    )
    restaurant = models.ForeignKey(
        Restaurant, 
        on_delete=models.CASCADE,
        related_name='user_visits'
    )
    last_visit = models.DateField(
        auto_now=True,
        help_text="Date of the most recent visit"
    )
    visit_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of visits to this restaurant"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "restaurant")
        ordering = ['-last_visit', '-visit_count']
        indexes = [
            models.Index(fields=['user', '-visit_count'], name='user_rest_visit_count_idx'),
            models.Index(fields=['user', '-last_visit'], name='user_rest_last_visit_idx'),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.restaurant.name} ({self.visit_count} visits)"


class UserCuisineStat(models.Model):
    """Model tracking how many times a user has visited restaurants of each cuisine type."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='cuisine_stats'
    )
    cuisine = models.ForeignKey(
        Cuisine, 
        on_delete=models.CASCADE,
        related_name='user_stats'
    )
    visit_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of visits to restaurants of this cuisine type"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "cuisine")
        ordering = ['-visit_count']
        indexes = [
            models.Index(fields=['user', '-visit_count'], name='user_cuisine_count_idx'),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.cuisine.name} ({self.visit_count} visits)"

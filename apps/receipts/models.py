import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


def receipt_upload_path(instance, filename):
    """
    Generate upload path for receipt images.
    Format: receipts/{user_id}/{date:%Y}/{date:%m}/{uuid4}.{ext}
    """
    # Get file extension
    ext = filename.split('.')[-1].lower()
    
    # Generate unique filename with UUID
    filename = f"{uuid.uuid4()}.{ext}"
    
    # Return the full path
    return f"receipts/{instance.user.id}/{instance.date.year}/{instance.date.month:02d}/{filename}"


class Receipt(models.Model):
    """Model representing a receipt uploaded by a user."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='receipts'
    )
    date = models.DateField(
        help_text="Date of the purchase"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Total price of the purchase"
    )
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        related_name='receipts',
        null=True,
        blank=True,
        help_text="Restaurant associated with this receipt"
    )

    restaurant_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of the restaurant"
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text="Address of the restaurant"
    )
    image = models.ImageField(
        upload_to=receipt_upload_path,
        help_text="Receipt image file"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date'], name='receipt_user_date_idx'),
            models.Index(fields=['user', '-date'], name='receipt_user_date_desc_idx'),
        ]

    def __str__(self):
        restaurant_name = self.restaurant.name if self.restaurant else self.restaurant_name
        return f"{restaurant_name} - {self.date} (${self.price})"

    @property
    def image_url(self):
        """Return the URL of the receipt image."""
        if self.image:
            return self.image.url
        return None

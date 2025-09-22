"""
Django signals for receipt models.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Receipt
from apps.restaurants.services.visit_tracking import update_visit_stats

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Receipt)
def update_visit_stats_on_receipt_creation(sender, instance, created, **kwargs):
    """
    Update user visit statistics when a receipt is created.

    This signal automatically tracks restaurant and cuisine visits
    whenever a new receipt is saved with a restaurant association.
    """
    if created and instance.restaurant:

        try:
            update_visit_stats(
                user=instance.user,
                restaurant=instance.restaurant,
                visit_date=instance.date,
            )
            logger.info(
                f"Updated visit stats for receipt {instance.id}: "
                f"{instance.user.email} -> {instance.restaurant.name}"
            )
        except Exception as e:
            logger.error(
                f"Failed to update visit stats for receipt {instance.id}: {str(e)}"
            )
            # Don't raise the exception to avoid breaking receipt creation
            # Visit stats are important but not critical to receipt functionality

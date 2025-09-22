"""
Service for tracking user restaurant and cuisine visit statistics.
"""

import logging
from django.db import transaction
from django.db.models import F
from apps.restaurants.models import UserRestaurantVisit, UserCuisineStat

logger = logging.getLogger(__name__)


def update_visit_stats(user, restaurant, visit_date):
    """
    Update user visit statistics for restaurant and cuisines.

    Args:
        user: User instance
        restaurant: Restaurant instance
        visit_date: Date of the visit
    """
    with transaction.atomic():
        # Update or create restaurant visit count
        restaurant_visit, created = UserRestaurantVisit.objects.get_or_create(
            user=user, restaurant=restaurant, defaults={"visit_count": 1}
        )

        if not created:
            # Increment visit count and update last visit date
            restaurant_visit.visit_count = F("visit_count") + 1
            restaurant_visit.save(update_fields=["visit_count"])
            # Refresh to get the updated count for logging
            restaurant_visit.refresh_from_db()

        logger.info(
            f"Updated restaurant visit: {user.email} -> {restaurant.name} "
            f"({restaurant_visit.visit_count} visits)"
        )

        # Update cuisine statistics for all cuisines of this restaurant
        restaurant_cuisines = restaurant.cuisines.all()

        for cuisine in restaurant_cuisines:
            cuisine_stat, created = UserCuisineStat.objects.get_or_create(
                user=user, cuisine=cuisine, defaults={"visit_count": 1}
            )

            if not created:
                # Increment cuisine visit count
                cuisine_stat.visit_count = F("visit_count") + 1
                cuisine_stat.save(update_fields=["visit_count"])
                # Refresh to get the updated count for logging
                cuisine_stat.refresh_from_db()

            logger.info(
                f"Updated cuisine stat: {user.email} -> {cuisine.name} "
                f"({cuisine_stat.visit_count} visits)"
            )


def get_user_restaurant_stats(user, limit=None):
    """
    Get user's restaurant visit statistics.

    Args:
        user: User instance
        limit: Optional limit for number of results

    Returns:
        QuerySet of UserRestaurantVisit ordered by visit count
    """
    queryset = UserRestaurantVisit.objects.filter(user=user).select_related(
        "restaurant"
    )

    if limit:
        queryset = queryset[:limit]

    return queryset


def get_user_cuisine_stats(user, limit=None):
    """
    Get user's cuisine visit statistics.

    Args:
        user: User instance
        limit: Optional limit for number of results

    Returns:
        QuerySet of UserCuisineStat ordered by visit count
    """
    queryset = UserCuisineStat.objects.filter(user=user).select_related("cuisine")

    if limit:
        queryset = queryset[:limit]

    return queryset


def get_user_top_restaurants(user, limit=10):
    """
    Get user's most visited restaurants.

    Args:
        user: User instance
        limit: Number of top restaurants to return

    Returns:
        List of tuples (restaurant, visit_count)
    """
    visits = UserRestaurantVisit.objects.filter(user=user).select_related("restaurant")[
        :limit
    ]
    return [(visit.restaurant, visit.visit_count) for visit in visits]


def get_user_top_cuisines(user, limit=10):
    """
    Get user's most visited cuisine types.

    Args:
        user: User instance
        limit: Number of top cuisines to return

    Returns:
        List of tuples (cuisine, visit_count)
    """
    stats = UserCuisineStat.objects.filter(user=user).select_related("cuisine")[:limit]
    return [(stat.cuisine, stat.visit_count) for stat in stats]

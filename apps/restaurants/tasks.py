import logging
from typing import Optional
from celery import shared_task
from django.utils import timezone
from django.db import transaction

from .models import Restaurant, Cuisine
from .services import GooglePlacesService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def update_restaurant_info(self, restaurant_id: str):
    """
    Update restaurant information from Google Places API.

    Args:
        restaurant_id: UUID of the restaurant to update
    """
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
        logger.info(
            f"Updating restaurant info for {restaurant.name} (ID: {restaurant_id})"
        )

        # Initialize Google Places service
        places_service = GooglePlacesService()

        # If this is a stub restaurant, try to find the real place_id first
        if restaurant.place_id.startswith("stub_"):
            logger.info(
                f"Found stub restaurant {restaurant.name}, searching for real place_id"
            )
            text_query = f"{restaurant.name}, {restaurant.address}"
            place_candidate = places_service.find_place_from_text(text_query)

            if place_candidate and place_candidate.get("place_id"):
                logger.info(
                    f"Found real place_id {place_candidate['place_id']} for stub {restaurant.name}"
                )
                restaurant.place_id = place_candidate["place_id"]
                restaurant.save(update_fields=["place_id"])
            else:
                logger.warning(
                    f"Could not find real place_id for stub restaurant {restaurant.name}"
                )
                return {
                    "status": "error",
                    "restaurant_id": restaurant_id,
                    "message": "Could not find real place_id for stub restaurant",
                }

        # Fetch updated data from Google Places
        data = places_service.fetch_restaurant_details(restaurant.place_id)

        if not data:
            logger.error(f"Failed to fetch data for restaurant {restaurant_id}")
            return {
                "status": "error",
                "restaurant_id": restaurant_id,
                "message": "Failed to fetch data from Google Places API",
            }

        print("--------------------------------")
        print("Data extracted from Google Places API:")
        print(data)
        print("--------------------------------")

        # Update restaurant with new data
        with transaction.atomic():
            updated_fields = []

            if data.get("name") and data["name"] != restaurant.name:
                restaurant.name = data["name"]
                updated_fields.append("name")

            if data.get("address") and data["address"] != restaurant.address:
                restaurant.address = data["address"]
                updated_fields.append("address")

            # Handle cuisines (many-to-many relationship)
            if data.get("cuisines"):
                current_cuisine_names = set(
                    restaurant.cuisines.values_list("name", flat=True)
                )
                new_cuisine_names = set(data["cuisines"])

                if current_cuisine_names != new_cuisine_names:
                    # Create cuisine objects if they don't exist
                    cuisine_objects = []
                    for cuisine_name in new_cuisine_names:
                        cuisine, created = Cuisine.objects.get_or_create(
                            name=cuisine_name
                        )
                        cuisine_objects.append(cuisine)

                    # Update the many-to-many relationship
                    restaurant.cuisines.set(cuisine_objects)
                    updated_fields.append("cuisines")

            if data.get("rating") and data["rating"] != restaurant.rating:
                restaurant.rating = data["rating"]
                updated_fields.append("rating")

            if data.get("latitude") and data["latitude"] != restaurant.latitude:
                restaurant.latitude = data["latitude"]
                updated_fields.append("latitude")

            if data.get("longitude") and data["longitude"] != restaurant.longitude:
                restaurant.longitude = data["longitude"]
                updated_fields.append("longitude")

            # Always update the updated_at timestamp
            restaurant.save()

            logger.info(
                f"Restaurant {restaurant_id} updated. Fields changed: {updated_fields}"
            )

            return {
                "status": "success",
                "restaurant_id": restaurant_id,
                "updated_fields": updated_fields,
                "restaurant_name": restaurant.name,
            }

    except Restaurant.DoesNotExist:
        logger.error(f"Restaurant with ID {restaurant_id} not found")
        return {
            "status": "error",
            "restaurant_id": restaurant_id,
            "message": "Restaurant not found",
        }

    except Exception as exc:
        logger.error(f"Error updating restaurant {restaurant_id}: {str(exc)}")

        # Retry the task with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2**self.request.retries * 60  # 1min, 2min, 4min
            logger.info(
                f"Retrying task in {countdown} seconds (attempt {self.request.retries + 1})"
            )
            raise self.retry(countdown=countdown, exc=exc)

        return {
            "status": "error",
            "restaurant_id": restaurant_id,
            "message": f"Task failed after {self.max_retries} retries: {str(exc)}",
        }


@shared_task
def update_all_restaurants():
    """
    Update all restaurants' information from Google Places API.
    This task is meant to be run periodically via Celery Beat.
    """
    logger.info("Starting bulk restaurant update task")

    restaurants = Restaurant.objects.all()
    total_count = restaurants.count()

    if total_count == 0:
        logger.info("No restaurants to update")
        return {
            "status": "success",
            "message": "No restaurants to update",
            "total_processed": 0,
        }

    # Queue individual update tasks for each restaurant
    task_ids = []
    for restaurant in restaurants:
        task = update_restaurant_info.delay(str(restaurant.id))
        task_ids.append(task.id)

    logger.info(f"Queued {len(task_ids)} restaurant update tasks")

    return {
        "status": "success",
        "message": f"Queued {len(task_ids)} restaurant update tasks",
        "total_processed": len(task_ids),
        "task_ids": task_ids,
    }


@shared_task
def create_restaurant_from_places_data(
    place_id: str, name: str, address: str
) -> Optional[str]:
    """
    Create a new restaurant record using Google Places data.

    Args:
        place_id: Google Places place_id
        name: Restaurant name (fallback)
        address: Restaurant address (fallback)

    Returns:
        Restaurant ID if created successfully, None otherwise
    """
    try:
        # Check if restaurant already exists
        existing_restaurant = Restaurant.objects.filter(place_id=place_id).first()
        if existing_restaurant:
            logger.info(f"Restaurant with place_id {place_id} already exists")
            return str(existing_restaurant.id)

        # Initialize Google Places service
        places_service = GooglePlacesService()

        # Try to fetch detailed data from Google Places
        data = places_service.fetch_restaurant_details(place_id)

        if data:
            # Create restaurant with Google Places data
            restaurant = Restaurant.objects.create(
                place_id=place_id,
                name=data.get("name", name),
                address=data.get("address", address),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                rating=data.get("rating"),
            )

            # Handle cuisines (many-to-many relationship)
            if data.get("cuisines"):
                cuisine_objects = []
                for cuisine_name in data["cuisines"]:
                    cuisine, created = Cuisine.objects.get_or_create(name=cuisine_name)
                    cuisine_objects.append(cuisine)
                restaurant.cuisines.set(cuisine_objects)

            logger.info(f"Created restaurant {restaurant.name} with Google Places data")
        else:
            # Create basic restaurant record with provided data
            restaurant = Restaurant.objects.create(
                place_id=place_id, name=name, address=address
            )
            logger.info(f"Created basic restaurant record for {name}")

            # Queue a task to update with Google Places data later
            update_restaurant_info.delay(str(restaurant.id))

        return str(restaurant.id)

    except Exception as e:
        logger.error(f"Error creating restaurant with place_id {place_id}: {str(e)}")
        return None

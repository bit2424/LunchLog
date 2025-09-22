"""
Integration tests for the complete lunch receipt and restaurant flow.

Tests the end-to-end journey from user registration to receipt creation
and Celery task execution for restaurant information updates.
"""

import time
import pytest
from decimal import Decimal
from unittest import mock
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from apps.receipts.models import Receipt
from apps.restaurants.models import Restaurant
from apps.restaurants.tasks import update_restaurant_info

User = get_user_model()


@pytest.mark.integration
def test_complete_user_flow_with_restaurant_creation(
    auth_client, test_receipt_data, mock_google_places_data, celery_eager
):
    """
    Test the complete flow:
    1. User registration and JWT auth (via auth_client fixture)
    2. Receipt creation with new restaurant
    3. Celery task execution for restaurant info update
    4. Data validation
    """
    with mock.patch("apps.restaurants.tasks.GooglePlacesService") as MockService:
        # Mock the Google Places Service methods
        mock_service_instance = MockService.return_value
        mock_service_instance.fetch_restaurant_details.return_value = (
            mock_google_places_data["place_details"]
        )
        mock_service_instance.find_place_from_text.return_value = (
            mock_google_places_data["find_place"]
        )

        response = auth_client.post(
            "/api/v1/receipts/", test_receipt_data, format="multipart"
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.data
    assert response.data["price"] == "25.99"
    assert response.data["restaurant_name"] == "Test Pizza Place"

    # Verify receipt was created in database
    receipt = Receipt.objects.get(id=response.data["id"])
    assert str(receipt.price) == "25.99"
    assert receipt.restaurant_name == "Test Pizza Place"

    # Verify restaurant was created
    assert Restaurant.objects.exists()
    restaurant = Restaurant.objects.first()
    assert restaurant.name == "Test Pizza Place"
    # Address should be updated by Celery task to the full Google Places format
    assert restaurant.address == "123 Main St, New York, NY 10001, USA"

    # Verify receipt is linked to restaurant
    receipt.refresh_from_db()
    assert receipt.restaurant is not None
    assert receipt.restaurant == restaurant

    # Verify restaurant info was updated by Celery task
    # (The task should have run synchronously due to CELERY_TASK_ALWAYS_EAGER=True)
    restaurant.refresh_from_db()

    assert restaurant.place_id == "ChIJTest123456789"
    assert restaurant.name == "Test Pizza Place"
    assert restaurant.address == "123 Main St, New York, NY 10001, USA"
    assert restaurant.latitude == 40.7128000
    assert restaurant.longitude == -74.0060000
    assert restaurant.rating == Decimal("4.50")


@pytest.mark.integration
def test_complete_user_flow_with_existing_restaurant(
    auth_client, test_receipt_data, test_restaurant, test_image
):
    """
    Test flow when restaurant already exists:
    1. Create user and get JWT (via auth_client fixture)
    2. Pre-create restaurant (via test_restaurant fixture)
    3. Create receipt with restaurant_id
    4. Verify linkage
    """
    # Create receipt with existing restaurant_id
    receipt_data = {
        "date": "2025-01-16",
        "price": "18.50",
        "restaurant_id": test_restaurant.id,
        "image": test_image,
    }

    with mock.patch("apps.restaurants.tasks.update_restaurant_info.delay") as mock_task:
        response = auth_client.post(
            "/api/v1/receipts/", receipt_data, format="multipart"
        )

    assert response.status_code == status.HTTP_201_CREATED

    # Verify receipt is linked to existing restaurant
    receipt = Receipt.objects.get(id=response.data["id"])
    assert receipt.restaurant == test_restaurant

    # Verify Celery task was triggered for restaurant update
    mock_task.assert_called_once_with(str(test_restaurant.id))


@pytest.mark.integration
def test_user_can_list_their_receipts(auth_client, test_receipt_data, image_factory):
    """Test that users can list their own receipts after creation."""
    # Create multiple receipts
    receipt_data_1 = test_receipt_data.copy()
    receipt_data_1.update({"image": image_factory(), "price": "15.99"})

    receipt_data_2 = test_receipt_data.copy()
    receipt_data_2.update(
        {
            "image": image_factory(),
            "price": "22.50",
        }
    )

    with mock.patch("apps.restaurants.tasks.GooglePlacesService"):
        response = auth_client.post(
            "/api/v1/receipts/", receipt_data_1, format="multipart"
        )
        assert response.status_code == status.HTTP_201_CREATED
        response = auth_client.post(
            "/api/v1/receipts/", receipt_data_2, format="multipart"
        )
        assert response.status_code == status.HTTP_201_CREATED

    # List receipts
    response = auth_client.get("/api/v1/receipts/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 2

    # Verify receipt data
    prices = [receipt["price"] for receipt in response.data["results"]]
    assert "15.99" in prices
    assert "22.50" in prices


@pytest.mark.integration
def test_user_can_search_restaurants(auth_client, test_restaurants):
    """Test that users can search and filter restaurants."""
    # Test search by name
    response = auth_client.get("/api/v1/restaurants/?search=pizza")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == "Mario's Pizza"

    # Test filter by cuisine
    response = auth_client.get("/api/v1/restaurants/?cuisine=Japanese")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    print(response.data["results"][0]["cuisines"])
    assert "Japanese" in [
        cuisine["name"] for cuisine in response.data["results"][0]["cuisines"]
    ]

    # Test filter by rating range
    response = auth_client.get("/api/v1/restaurants/?rating_min=4.5")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2  # Pizza (4.5) and Sushi (4.8)


@pytest.mark.integration
def test_celery_task_updates_stub_restaurant(db, mock_google_places_data):
    """Test that Celery task correctly updates a stub restaurant."""
    # Create a stub restaurant (as would be created during receipt creation)
    stub_restaurant = Restaurant.objects.create(
        place_id="stub_1234567890abcdef",
        name="Stub Restaurant",
        address="Partial Address",
        latitude=None,
        longitude=None,
        rating=None,
    )

    with mock.patch("apps.restaurants.tasks.GooglePlacesService") as MockService:
        # Mock the Google Places Service methods
        mock_service_instance = MockService.return_value
        mock_service_instance.find_place_from_text.return_value = (
            mock_google_places_data["find_place"]
        )
        mock_service_instance.fetch_restaurant_details.return_value = (
            mock_google_places_data["place_details"]
        )

        # Execute the Celery task
        update_restaurant_info(str(stub_restaurant.id))

    # Verify restaurant was updated
    stub_restaurant.refresh_from_db()
    assert stub_restaurant.place_id == "ChIJTest123456789"
    assert stub_restaurant.name == "Test Pizza Place"
    assert stub_restaurant.address == "123 Main St, New York, NY 10001, USA"
    assert stub_restaurant.latitude == 40.7128000
    assert stub_restaurant.longitude == -74.0060000
    assert stub_restaurant.rating == Decimal("4.50")


@pytest.mark.integration
def test_celery_task_handles_api_errors_gracefully(db):
    """Test that Celery task handles Google Places API errors gracefully."""
    restaurant = Restaurant.objects.create(
        place_id="ChIJTest123456789", name="Test Restaurant", address="Test Address"
    )

    # Mock service to return None (simulating API error)
    with mock.patch("apps.restaurants.tasks.GooglePlacesService") as MockService:
        mock_service_instance = MockService.return_value
        mock_service_instance.fetch_restaurant_details.return_value = None

        # Task should not crash, but restaurant should remain unchanged
        original_name = restaurant.name
        try:
            update_restaurant_info(str(restaurant.id))
        except Exception:
            # Task might retry and eventually fail, which is expected
            pass

    restaurant.refresh_from_db()
    # Restaurant should still exist and have original data
    assert restaurant.name == original_name


@pytest.mark.integration
def test_unauthenticated_requests_are_blocked(db):
    """Test that protected endpoints require authentication."""
    client = APIClient()  # Unauthenticated client

    # Test protected endpoints
    protected_endpoints = [
        "/api/v1/receipts/",
        "/api/v1/restaurants/",
        "/api/v1/me/",
    ]

    for endpoint in protected_endpoints:
        response = client.get(endpoint)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


@pytest.mark.integration
def test_invalid_jwt_token_is_rejected(db):
    """Test that invalid JWT tokens are rejected."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_here")

    response = client.get("/api/v1/me/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
def test_celery_scheduled_job_execution(db, mock_google_places_data, celery_eager):
    """Test that Celery accepts a scheduled job and executes it in tests (eager)."""

    # Create a restaurant that needs updating
    restaurant = Restaurant.objects.create(
        place_id="ChIJTest123456789",
        name="Test Restaurant",
        address="Original Address",
        rating=None,
    )

    restaurant.refresh_from_db()

    # Mock the Google Places service for the scheduled task
    with mock.patch("apps.restaurants.tasks.GooglePlacesService") as MockService:
        mock_service_instance = MockService.return_value
        mock_service_instance.find_place_from_text.return_value = (
            mock_google_places_data["find_place"]
        )
        mock_service_instance.fetch_restaurant_details.return_value = (
            mock_google_places_data["place_details"]
        )

        # Schedule the task with countdown; in eager mode, it executes immediately
        result = update_restaurant_info.apply_async(
            args=[str(restaurant.id)], countdown=3
        ).get()

        print("--------------------------------")
        print("Result from Celery task:")
        print(result)
        print("--------------------------------")
        assert result["status"] == "success"
        assert result["restaurant_id"] == str(restaurant.id)

        # Verify the restaurant was actually updated
        restaurant.refresh_from_db()
        assert restaurant.name == "Test Pizza Place"  # Should be updated from mock data
        assert restaurant.address == "123 Main St, New York, NY 10001, USA"


@pytest.mark.integration
@pytest.mark.external
def test_live_google_places_creates_and_updates_restaurant(
    db, external_api_key, celery_eager, jwt_client, test_image
):
    """Live test against Google Places API: creates a stub and verifies update fills details.
    Skips if GOOGLE_PLACES_API_KEY is not configured.
    """
    client = jwt_client

    # Use a well-known place likely to be found
    receipt_payload = {
        "date": "2025-01-15",
        "price": "12.34",
        "restaurant_name": "Joe's Pizza",
        "address": "7 Carmine St, New York, NY 10014",
        "image": test_image,
    }

    create_resp = client.post("/api/v1/receipts/", receipt_payload, format="multipart")
    assert create_resp.status_code == status.HTTP_201_CREATED

    # Validate database state
    receipt = Receipt.objects.get(id=create_resp.data["id"])
    assert receipt.restaurant is not None
    restaurant = receipt.restaurant

    restaurant.refresh_from_db()
    assert restaurant.place_id is not None
    assert not restaurant.place_id.startswith("stub_")
    # Basic sanity checks that details were populated
    assert restaurant.name is not None and len(restaurant.name) > 0
    assert restaurant.address is not None and len(restaurant.address) > 0
    # lat/lng should be set for a real place
    assert restaurant.latitude is not None
    assert restaurant.longitude is not None

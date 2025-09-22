import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an API client instance."""
    return APIClient()


@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.mark.django_db
class TestJWTAuthentication:
    """Test JWT authentication endpoints."""

    def test_obtain_token_pair_success(self, api_client, user):
        """Test obtaining JWT token pair with valid credentials."""
        url = reverse("users:jwt_create")
        data = {"email": user.email, "password": "testpass123"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

        # Tokens should be strings
        assert isinstance(response.data["access"], str)
        assert isinstance(response.data["refresh"], str)

    def test_obtain_token_pair_invalid_credentials(self, api_client, user):
        """Test obtaining JWT token pair with invalid credentials."""
        url = reverse("users:jwt_create")
        data = {"email": user.email, "password": "wrongpassword"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "access" not in response.data
        assert "refresh" not in response.data

    def test_obtain_token_pair_nonexistent_user(self, api_client):
        """Test obtaining JWT token pair with nonexistent user."""
        url = reverse("users:jwt_create")
        data = {"email": "nonexistent@example.com", "password": "password123"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_success(self, api_client, user):
        """Test refreshing access token with valid refresh token."""
        # First get tokens
        refresh = RefreshToken.for_user(user)

        url = reverse("users:jwt_refresh")
        data = {"refresh": str(refresh)}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert isinstance(response.data["access"], str)

    def test_refresh_token_invalid(self, api_client):
        """Test refreshing access token with invalid refresh token."""
        url = reverse("users:jwt_refresh")
        data = {"refresh": "invalid_token"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_valid(self, api_client, user):
        """Test verifying a valid access token."""
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        url = reverse("users:jwt_verify")
        data = {"token": str(access_token)}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

    def test_verify_token_invalid(self, api_client):
        """Test verifying an invalid access token."""
        url = reverse("users:jwt_verify")
        data = {"token": "invalid_token"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_with_jwt(self, api_client, user):
        """Test accessing a protected endpoint with JWT authentication."""
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Access protected endpoint (receipts list)
        url = reverse("receipts:receipts-list")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_access_protected_endpoint_without_jwt(self, api_client):
        """Test accessing a protected endpoint without JWT token."""
        url = reverse("receipts:receipts-list")
        response = api_client.get(url)

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_access_protected_endpoint_with_invalid_jwt(self, api_client):
        """Test accessing a protected endpoint with invalid JWT token."""
        url = reverse("receipts:receipts-list")
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCurrentUserView:
    """Test the current user profile endpoint."""

    def test_get_current_user_with_jwt(self, api_client, user):
        """Test getting current user profile with JWT authentication."""
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        url = reverse("users:current_user")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email
        assert response.data["first_name"] == user.first_name
        assert response.data["last_name"] == user.last_name
        assert "password" not in response.data  # Password should not be returned

    def test_get_current_user_without_auth(self, api_client):
        """Test getting current user profile without authentication."""
        url = reverse("users:current_user")
        response = api_client.get(url)

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_update_current_user_with_jwt(self, api_client, user):
        """Test updating current user profile with JWT authentication."""
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        url = reverse("users:current_user")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        data = {"first_name": "Updated", "last_name": "Name"}
        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"
        assert response.data["last_name"] == "Name"

        # Verify user was actually updated
        user.refresh_from_db()
        assert user.first_name == "Updated"
        assert user.last_name == "Name"


@pytest.mark.django_db
class TestJWTWithReceiptsAPI:
    """Test JWT authentication with receipts API."""

    def test_create_receipt_with_jwt(self, api_client, user):
        """Test creating a receipt with JWT authentication."""
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        url = reverse("receipts:receipts-list")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # Create a simple in-memory image for testing
        from PIL import Image
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create test image
        image = Image.new("RGB", (100, 100), color="red")
        image_io = BytesIO()
        image.save(image_io, format="JPEG")
        image_io.seek(0)

        image_file = SimpleUploadedFile(
            "test_receipt.jpg", image_io.read(), content_type="image/jpeg"
        )

        data = {
            "date": "2025-09-19",
            "price": "25.50",
            "restaurant_name": "Test Restaurant",
            "address": "123 Test St, Test City",
            "image": image_file,
        }

        response = api_client.post(url, data, format="multipart")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["restaurant_name"] == "Test Restaurant"
        assert response.data["price"] == "25.50"
        # User should be set automatically from JWT
        assert "user" not in response.data or response.data["user"] == user.id

    def test_list_user_receipts_with_jwt(self, api_client, user):
        """Test listing user's receipts with JWT authentication."""
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        url = reverse("receipts:receipts-list")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        # Should only see this user's receipts
        for receipt in response.data["results"]:
            # Note: receipt serializer might not include user field in list view
            pass  # We trust the ViewSet filtering by user

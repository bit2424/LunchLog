import pytest
import tempfile
from PIL import Image
from io import BytesIO
from datetime import date
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.receipts.models import Receipt

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_password():
    return "strong-test-pass"


@pytest.fixture
def test_user(db, test_password):
    user = User.objects.create_user(
        email="testuser@example.com", password=test_password
    )
    return user


@pytest.fixture
def test_user2(db, test_password):
    user = User.objects.create_user(
        email="testuser2@example.com", password=test_password
    )
    return user


@pytest.fixture
def auth_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def test_image():
    """Create a test image file."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as img_file:
        # Create a small test image
        image = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)

        # Create Django's SimpleUploadedFile
        image_file = SimpleUploadedFile(
            name="test.jpg", content=buffer.getvalue(), content_type="image/jpeg"
        )
        return image_file


@pytest.fixture
def test_receipt_data(test_image):
    """Create test receipt data."""
    return {
        "date": date.today(),
        "price": "15.99",
        "restaurant_name": "Test Restaurant",
        "address": "123 Test St, Test City",
        "image": test_image,
    }


@pytest.fixture
def test_receipt(db, test_user, test_receipt_data):
    """Create a test receipt in the database."""
    receipt_data = test_receipt_data.copy()
    receipt = Receipt.objects.create(
        user=test_user,
        date=receipt_data["date"],
        price=Decimal(receipt_data["price"]),
        restaurant_name=receipt_data["restaurant_name"],
        address=receipt_data["address"],
        image=receipt_data["image"],
    )
    return receipt

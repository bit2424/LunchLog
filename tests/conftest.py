import pytest
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from apps.restaurants.models import Restaurant
from apps.receipts.models import Receipt


User = get_user_model()


@pytest.fixture
def test_user_data():
    """Return test user registration data."""
    return {
        'email': 'testuser@example.com',
        'password': 'testpassword123',
        'first_name': 'Test',
        'last_name': 'User'
    }


@pytest.fixture
def test_receipt_data(test_image):
    """Return test receipt data with image."""
    return {
        'date': '2025-01-15',
        'price': '25.99',
        'restaurant_name': 'Test Pizza Place',
        'address': '123 Main St, New York, NY 10001',
        'image': test_image
    }


@pytest.fixture
def mock_google_places_data():
    """Return mock Google Places API response data."""
    return {
        'place_details': {
            'place_id': 'ChIJTest123456789',
            'name': 'Test Pizza Place',
            'address': '123 Main St, New York, NY 10001, USA',
            'latitude': Decimal('40.7128000'),
            'longitude': Decimal('-74.0060000'),
            'rating': Decimal('4.50'),
            'cuisine': 'Italian',
        },
        'find_place': {
            'place_id': 'ChIJTest123456789',
            'name': 'Test Pizza Place',
            'formatted_address': '123 Main St, New York, NY 10001, USA',
            'geometry': {'location': {'lat': 40.7128, 'lng': -74.0060}}
        }
    }


@pytest.fixture
def test_restaurant():
    """Create and return a test restaurant."""
    restaurant = Restaurant.objects.create(
        place_id='ChIJExisting123456',
        name='Existing Restaurant',
        address='456 Existing St, NY',
        latitude=Decimal('40.7580'),
        longitude=Decimal('-73.9855'),
        cuisine='American',
        rating=Decimal('4.2')
    )
    return restaurant


@pytest.fixture
def test_restaurants():
    """Create and return a set of test restaurants for search/filter tests."""
    restaurants = [
        Restaurant.objects.create(
            place_id='pizza1',
            name='Mario\'s Pizza',
            address='123 Pizza St',
            cuisine='Italian',
            rating=Decimal('4.5')
        ),
        Restaurant.objects.create(
            place_id='burger1',
            name='Burger Palace',
            address='456 Burger Ave',
            cuisine='American',
            rating=Decimal('4.0')
        ),
        Restaurant.objects.create(
            place_id='sushi1',
            name='Sushi Express',
            address='789 Sushi Rd',
            cuisine='Japanese',
            rating=Decimal('4.8')
        )
    ]
    return restaurants


@pytest.fixture
def auth_client(db):
    """Return an APIClient with a registered and authenticated user."""
    client = APIClient()
    user_data = {
        'email': 'testuser@example.com',
        'password': 'testpassword123',
        'first_name': 'Test',
        'last_name': 'User'
    }
    
    # Register user
    signup_resp = client.post('/api/v1/auth/signup/', user_data)
    assert signup_resp.status_code == status.HTTP_201_CREATED
    
    # Get JWT token
    jwt_resp = client.post('/api/v1/auth/jwt/create/', {
        'email': user_data['email'],
        'password': user_data['password']
    })
    assert jwt_resp.status_code == status.HTTP_200_OK
    access_token = jwt_resp.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    return client


@pytest.fixture
def external_api_key(settings):
    """Ensure a Google Places API key exists or skip external tests."""
    api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', None)
    if not api_key:
        pytest.skip("GOOGLE_PLACES_API_KEY not set; skipping external test")
    return api_key


@pytest.fixture
def celery_eager(settings):
    """Run Celery tasks eagerly and propagate exceptions for tests."""
    original_eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
    original_propagate = getattr(settings, 'CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS', False)
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS = True
    try:
        yield
    finally:
        settings.CELERY_TASK_ALWAYS_EAGER = original_eager
        settings.CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS = original_propagate


@pytest.fixture
def jwt_client(db):
    """Return an APIClient authenticated with a JWT access token."""
    client = APIClient()

    # Create or ensure user exists
    email = 'externaltest@example.com'
    password = 'external-test-pass-123'
    if not User.objects.filter(email=email).exists():
        User.objects.create_user(email=email, password=password)

    # Obtain JWT token via API to simulate real flow
    login_resp = client.post('/api/v1/auth/jwt/create/', {
        'email': email,
        'password': password
    })
    assert login_resp.status_code == status.HTTP_200_OK
    access_token = login_resp.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    return client


@pytest.fixture
def test_image():
    """Provide a small valid JPEG image for upload tests."""
    image = Image.new('RGB', (50, 50), color='blue')
    buffer = BytesIO()
    image.save(buffer, 'JPEG')
    buffer.seek(0)
    return SimpleUploadedFile(
        name='test_upload.jpg',
        content=buffer.getvalue(),
        content_type='image/jpeg'
    )

@pytest.fixture
def image_factory():
    def _make(name='test_upload.jpg', color='blue'):
        image = Image.new('RGB', (50, 50), color=color)
        buffer = BytesIO()
        image.save(buffer, 'JPEG')
        buffer.seek(0)
        return SimpleUploadedFile(name=name, content=buffer.getvalue(), content_type='image/jpeg')
    return _make
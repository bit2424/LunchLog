from io import BytesIO
from PIL import Image
import pytest
from datetime import date
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory
from apps.receipts.serializers import (
    ReceiptSerializer,
    ReceiptCreateSerializer,
    ReceiptListSerializer
)

pytestmark = pytest.mark.django_db

@pytest.fixture
def request_context(test_user):
    factory = APIRequestFactory()
    request = factory.get('/')
    request.user = test_user
    return {'request': request}

def test_receipt_serializer_create(test_user, test_receipt_data, request_context):
    """Test creating a receipt using the serializer."""
    serializer = ReceiptSerializer(data=test_receipt_data, context=request_context)
    assert serializer.is_valid()
    
    receipt = serializer.save()
    assert receipt.user == test_user
    assert receipt.price == Decimal(test_receipt_data['price'])
    assert receipt.restaurant_name == test_receipt_data['restaurant_name']

def test_receipt_serializer_read(test_receipt):
    """Test reading a receipt using the serializer."""
    serializer = ReceiptSerializer(test_receipt)
    data = serializer.data
    
    assert data['id'] == test_receipt.id
    assert data['price'] == str(test_receipt.price)
    assert data['restaurant_name'] == test_receipt.restaurant_name
    assert 'image_url' in data
    assert 'image' not in data  # Image field should be removed in representation

def test_receipt_create_serializer_validation(test_receipt_data):
    """Test validation in ReceiptCreateSerializer."""
    # Test without image
    data = test_receipt_data.copy()
    data['image'] = None
    serializer = ReceiptCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert 'image' in serializer.errors

    # Test with invalid price
    data = test_receipt_data.copy()
    data['price'] = '-1.00'
    serializer = ReceiptCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert 'price' in serializer.errors

    # Test with invalid date format
    data = test_receipt_data.copy()
    data['date'] = 'invalid-date'
    serializer = ReceiptCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert 'date' in serializer.errors

def test_receipt_create_serializer_file_validation(test_receipt_data):
    """Test file validation in ReceiptCreateSerializer."""
    # Test with oversized file
    file = BytesIO()
    image = Image.new("RGB", (10000, 9000), (255, 0, 0))
    image.save(file, "JPEG", quality=1000)  # max quality -> bigger file
    file_size = file.tell()
    file.seek(0)
    
    large_file = SimpleUploadedFile(
        "large.jpg",
        file.getvalue(),  # More than 1MB
        content_type="image/jpeg"
    )
    data = test_receipt_data.copy()
    data['image'] = large_file
    serializer = ReceiptCreateSerializer(data=data)
    
    result = serializer.is_valid()
    
    assert not result
    assert 'image' in serializer.errors
    assert 'too large' in str(serializer.errors['image'][0])

    # Test with invalid file type
    
    invalid_file = SimpleUploadedFile(
        "test.txt",
        b"hello world",
        content_type="text/plain"
    )
    data = test_receipt_data.copy()
    data['image'] = invalid_file
    serializer = ReceiptCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert 'image' in serializer.errors
    assert 'The file you uploaded was either not an image or a corrupted image.' in str(serializer.errors['image'][0])
    
    file = BytesIO()
    image = Image.new("RGB", (1000, 100), (255, 0, 0))
    image.save(file, "TIFF", quality=1000)  # max quality -> bigger file
    file_size = file.tell()
    file.seek(0)
    
    large_file = SimpleUploadedFile(
        "normal_image.tiff",
        file.getvalue(),  # More than 1MB
        content_type="image/tiff"
    )
    data = test_receipt_data.copy()
    data['image'] = large_file
    serializer = ReceiptCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert 'image' in serializer.errors
    assert 'Unsupported image format' in str(serializer.errors['image'][0])

def test_receipt_list_serializer(test_receipt):
    """Test the list serializer."""
    serializer = ReceiptListSerializer(test_receipt)
    data = serializer.data
    
    # Check that only the specified fields are included
    expected_fields = {
        'id', 'date', 'price', 'restaurant_name',
        'address', 'image_url', 'created_at'
    }
    assert set(data.keys()) == expected_fields
    
    # Verify field values
    assert data['id'] == test_receipt.id
    assert data['price'] == str(test_receipt.price)
    assert data['restaurant_name'] == test_receipt.restaurant_name
    assert 'image_url' in data

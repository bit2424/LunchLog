import pytest
from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from apps.receipts.models import Receipt, receipt_upload_path
from django.db import connection

pytestmark = pytest.mark.django_db

def test_receipt_creation(test_user, test_receipt_data):
    """Test creating a receipt."""
    receipt = Receipt.objects.create(
        user=test_user,
        date=test_receipt_data['date'],
        price=Decimal(test_receipt_data['price']),
        restaurant_name=test_receipt_data['restaurant_name'],
        address=test_receipt_data['address'],
        image=test_receipt_data['image']
    )
    
    assert receipt.pk is not None
    assert receipt.user == test_user
    assert receipt.price == Decimal('15.99')
    assert receipt.restaurant_name == 'Test Restaurant'


def test_receipt_image_url(test_receipt):
    """Test the image_url property."""
    assert test_receipt.image_url is not None
    assert isinstance(test_receipt.image_url, str)

def test_receipt_price_validation():
    """Test price validation."""
    with pytest.raises(ValidationError):
        Receipt(price=Decimal('-1.00')).full_clean()
    
    with pytest.raises(ValidationError):
        Receipt(price=Decimal('0.00')).full_clean()
    
    # Valid price should not raise ValidationError
    receipt = Receipt(price=Decimal('0.01'))
    receipt.full_clean(exclude=['user', 'date', 'restaurant_name', 'address', 'image'])

def test_receipt_indexes(test_user):
    test_date = date.today()
    Receipt.objects.create(
        user=test_user,
        date=test_date,
        price=Decimal('10.00'),
        restaurant_name='Test Restaurant',
        address='Test Address',
        image='test.jpg'
    )

    with connection.cursor() as cursor:
        cursor.execute("""
            EXPLAIN SELECT 1 FROM receipts_receipt
            WHERE date = %s AND user_id = %s LIMIT 1;
        """, [test_date, test_user.id])
        plan = cursor.fetchall()

    # Flatten plan text and assert our index name is mentioned
    plan_text = " ".join(row[0] for row in plan)
    print(plan_text)
    assert "receipt_user_date_desc_idx" in plan_text
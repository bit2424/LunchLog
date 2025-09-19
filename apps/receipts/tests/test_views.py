import pytest
from datetime import date
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from apps.receipts.models import Receipt

pytestmark = pytest.mark.django_db


RECEIPT_URL = reverse('receipts:receipts-list')
RECEIPT_DETAIL_URL = lambda pk: reverse('receipts:receipts-detail', args=[pk])
RECEIPT_MONTHLY_SUMMARY_URL = reverse('receipts:receipts-monthly-summary')



def test_create_receipt(auth_client, test_receipt_data):
    """Test creating a receipt via API."""
    url = RECEIPT_URL
    response = auth_client.post(url, test_receipt_data, format='multipart')
    
    assert response.status_code == status.HTTP_201_CREATED
    assert 'id' in response.data
    assert 'image_url' in response.data
    assert 'image' not in response.data
    assert response.data['restaurant_name'] == test_receipt_data['restaurant_name']
    assert response.data['price'] == test_receipt_data['price']

def test_create_receipt_unauthenticated(api_client, test_receipt_data):
    """Test that unauthenticated users cannot create receipts."""
    url = RECEIPT_URL
    response = api_client.post(url, test_receipt_data, format='multipart')
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_list_receipts(auth_client, test_user):
    """Test listing user's receipts."""
    url = RECEIPT_URL
    
    receipt2 = Receipt.objects.create(
        user=test_user,
        date=date.today(),
        price=Decimal('20.00'),
        restaurant_name='Other User Restaurant 2',
        address='Test Address 2',
        image='test 2.jpg'
    )
    
    receipt1 = Receipt.objects.create(
        user=test_user,
        date=date.today(),
        price=Decimal('10.00'),
        restaurant_name='Other User Restaurant',
        address='Test Address',
        image='test.jpg'
    )
    
    
    response = auth_client.get(url)
    
    print(response.data)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 2
    assert response.data['results'][0]['id'] == receipt1.id
    assert response.data['results'][0]['restaurant_name'] == receipt1.restaurant_name
    assert response.data['results'][1]['id'] == receipt2.id
    assert response.data['results'][1]['restaurant_name'] == receipt2.restaurant_name

def test_list_receipts_monthly_filter(auth_client, test_user):
    """Test listing receipts with monthly filter."""
    # Create receipts in different months
    Receipt.objects.create(
        user=test_user,
        date='2024-01-15',
        price=Decimal('10.00'),
        restaurant_name='Jan Restaurant',
        address='Test Address',
        image='test1.jpg'
    )
    Receipt.objects.create(
        user=test_user,
        date='2024-02-15',
        price=Decimal('20.00'),
        restaurant_name='Feb Restaurant',
        address='Test Address',
        image='test2.jpg'
    )
    
    # Test January filter
    url = RECEIPT_URL
    response = auth_client.get(url, {'month': '2024-01'})
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert response.data['results'][0]['restaurant_name'] == 'Jan Restaurant'
    
    # Test February filter
    response = auth_client.get(url, {'month': '2024-02'})
    assert response.data['count'] == 1
    assert response.data['results'][0]['restaurant_name'] == 'Feb Restaurant'
    
    # Test invalid month format
    response = auth_client.get(url, {'month': 'invalid'})
    assert response.data['count'] == 0

def test_retrieve_receipt(auth_client, test_user):
    """Test retrieving a specific receipt."""
    receipt = Receipt.objects.create(
        user=test_user,
        date=date.today(),
        price=Decimal('10.00'),
        restaurant_name='Other User Restaurant',
        address='Test Address',
        image='test.jpg'
    )
    
    url = RECEIPT_DETAIL_URL(receipt.id)
    response = auth_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == receipt.id
    assert response.data['restaurant_name'] == receipt.restaurant_name

def test_retrieve_receipt_other_user(auth_client, test_user2):
    """Test that users cannot retrieve other users' receipts."""
    # Create receipt for other user
    receipt = Receipt.objects.create(
        user=test_user2,
        date=date.today(),
        price=Decimal('10.00'),
        restaurant_name='Other User Restaurant',
        address='Test Address',
        image='test.jpg'
    )
    
    url = RECEIPT_DETAIL_URL(receipt.id)
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_receipt(auth_client, test_user, test_receipt_data):
    """Test updating a receipt."""
    receipt = Receipt.objects.create(
        user=test_user,
        date=test_receipt_data['date'],
        price=test_receipt_data['price'],
        restaurant_name=test_receipt_data['restaurant_name'],
        address=test_receipt_data['address'],
        image=test_receipt_data['image']
    )
    url = RECEIPT_DETAIL_URL(receipt.id)
    updated_data = {}
    updated_data['restaurant_name'] = 'Updated Restaurant'
    
    response = auth_client.patch(url, updated_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['restaurant_name'] == 'Updated Restaurant'

def test_delete_receipt(auth_client,test_receipt):
    """Test deleting a receipt."""
    url = RECEIPT_DETAIL_URL(test_receipt.id)
    response = auth_client.delete(url)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Receipt.objects.filter(id=test_receipt.id).exists()

def test_monthly_summary(auth_client, test_user):
    """Test the monthly summary endpoint."""
    # Create test receipts
    Receipt.objects.create(
        user=test_user,
        date='2024-03-15',
        price=Decimal('10.00'),
        restaurant_name='Restaurant 1',
        address='Address 1',
        image='test1.jpg'
    )
    Receipt.objects.create(
        user=test_user,
        date='2024-03-20',
        price=Decimal('20.00'),
        restaurant_name='Restaurant 2',
        address='Address 2',
        image='test2.jpg'
    )
    
    url = RECEIPT_MONTHLY_SUMMARY_URL
    response = auth_client.get(url, {'month': '2024-03'})
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['month'] == '2024-03'
    assert response.data['total_count'] == 2
    assert response.data['total_amount'] == '30.00'
    assert len(response.data['receipts']) == 2

def test_monthly_summary_invalid_month(auth_client):
    """Test monthly summary with invalid month format."""
    url = RECEIPT_MONTHLY_SUMMARY_URL
    
    # Test missing month parameter
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Test invalid month format
    response = auth_client.get(url, {'month': 'invalid'})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

SIGNUP_URL = reverse('users:signup')
LOGIN_URL = reverse('users:login')


class PublicUserApiTests(TestCase):
    """Test the users public API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful."""
        res = self.client.post(SIGNUP_URL, self.user_data)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        # Check user exists in database
        user = get_user_model().objects.get(email=self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))
        
        # Check response doesn't contain password
        self.assertNotIn('password', res.data)
        
        # Check session is created (user is logged in)
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(
            int(self.client.session['_auth_user_id']),
            user.id
        )

    def test_create_user_with_existing_email(self):
        """Test creating a user that already exists fails."""
        # Create user with email
        get_user_model().objects.create_user(**self.user_data)

        res = self.client.post(SIGNUP_URL, self.user_data)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res.data)

    def test_password_too_short(self):
        """Test that the password must be more than 8 characters."""
        payload = self.user_data.copy()
        payload['password'] = 'pw'
        res = self.client.post(SIGNUP_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', res.data)
        
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_login_valid_credentials(self):
        """Test that a valid login creates a session."""
        # Create user
        get_user_model().objects.create_user(**self.user_data)

        # Login
        payload = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        res = self.client.post(LOGIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('id', res.data)
        self.assertEqual(res.data['email'], self.user_data['email'])
        
        # Check session is created
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_invalid_credentials(self):
        """Test that login fails with invalid credentials."""
        # Create user
        get_user_model().objects.create_user(**self.user_data)

        # Try to login with wrong password
        payload = {
            'email': self.user_data['email'],
            'password': 'wrongpass'
        }
        res = self.client.post(LOGIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_nonexistent_user(self):
        """Test that login fails for a user that doesn't exist."""
        payload = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        res = self.client.post(LOGIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('_auth_user_id', self.client.session)

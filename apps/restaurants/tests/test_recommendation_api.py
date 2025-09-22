"""
Test cases for restaurant recommendation API endpoints.
"""

import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.restaurants.models import (
    Restaurant,
    Cuisine,
    UserRestaurantVisit,
    UserCuisineStat,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestRecommendationAPIEndpoints:
    """Test cases for recommendation API endpoints."""

    @pytest.fixture
    def authenticated_client(self):
        """Create an authenticated API client."""
        user = User.objects.create_user(email="test@example.com", password="test123")
        client = APIClient()
        client.force_authenticate(user=user)
        return client, user

    @pytest.fixture
    def setup_user_data(self, authenticated_client):
        """Set up test data for the authenticated user."""
        client, user = authenticated_client

        # Create cuisines
        italian_cuisine = Cuisine.objects.create(name="Italian")
        chinese_cuisine = Cuisine.objects.create(name="Chinese")

        # Create restaurants with coordinates
        restaurant1 = Restaurant.objects.create(
            place_id="place1",
            name="User Favorite Italian",
            address="123 Test St",
            latitude=40.7128,
            longitude=-74.0060,
        )
        restaurant1.cuisines.set([italian_cuisine])

        restaurant2 = Restaurant.objects.create(
            place_id="place2",
            name="User Favorite Chinese",
            address="456 Test Ave",
            latitude=40.7589,
            longitude=-73.9851,
        )
        restaurant2.cuisines.set([chinese_cuisine])

        # Create visit history
        UserRestaurantVisit.objects.create(
            user=user, restaurant=restaurant1, visit_count=5
        )
        UserRestaurantVisit.objects.create(
            user=user, restaurant=restaurant2, visit_count=3
        )

        # Create cuisine stats
        UserCuisineStat.objects.create(
            user=user, cuisine=italian_cuisine, visit_count=5
        )
        UserCuisineStat.objects.create(
            user=user, cuisine=chinese_cuisine, visit_count=3
        )

        return client, user

    @pytest.mark.integration
    @patch(
        "apps.restaurants.services.GooglePlacesService.get_recommendations_near_location"
    )
    def test_good_recommendations_endpoint(self, mock_recommendations, setup_user_data):
        """Test the good recommendations API endpoint."""
        client, user = setup_user_data

        # Mock the Google Places response
        mock_recommendations.side_effect = [
            [
                {
                    "place_id": "good1",
                    "name": "Excellent Restaurant",
                    "rating": 4.7,
                    "vicinity": "Near favorite spot",
                    "cuisines": ["Italian Restaurant"],
                    "business_status": "OPERATIONAL",
                }
            ],
            [],  # No recommendations from second location
        ]

        url = reverse("restaurants:restaurant-good-recommendations")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["recommendation_type"] == "good"
        assert data["count"] == 1
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["name"] == "Excellent Restaurant"
        assert data["recommendations"][0]["recommendation_type"] == "good"

        # Check user context
        assert "user_context" in data
        assert "frequent_restaurants" in data["user_context"]
        assert len(data["user_context"]["frequent_restaurants"]) > 0

    @pytest.mark.integration
    @patch(
        "apps.restaurants.services.GooglePlacesService.get_recommendations_near_location"
    )
    def test_cheap_recommendations_endpoint(
        self, mock_recommendations, setup_user_data
    ):
        """Test the cheap recommendations API endpoint."""
        client, user = setup_user_data

        # Mock the Google Places response
        mock_recommendations.side_effect = [
            [
                {
                    "place_id": "cheap1",
                    "name": "Budget Eats",
                    "rating": 3.8,
                    "price_level": 1,
                    "vicinity": "Affordable dining",
                    "cuisines": ["Restaurant"],
                    "business_status": "OPERATIONAL",
                }
            ],
            [],
        ]

        url = reverse("restaurants:restaurant-cheap-recommendations")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["recommendation_type"] == "cheap"
        assert data["count"] == 1
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["name"] == "Budget Eats"
        assert data["recommendations"][0]["recommendation_type"] == "cheap"

    @pytest.mark.integration
    @patch(
        "apps.restaurants.services.GooglePlacesService.get_recommendations_near_location"
    )
    def test_cuisine_match_recommendations_endpoint(
        self, mock_recommendations, setup_user_data
    ):
        """Test the cuisine match recommendations API endpoint."""
        client, user = setup_user_data

        # Mock the Google Places response
        mock_recommendations.side_effect = [
            [
                {
                    "place_id": "match1",
                    "name": "New Italian Place",
                    "rating": 4.3,
                    "vicinity": "Italian cuisine",
                    "cuisines": ["Italian Restaurant", "Pizza Restaurant"],
                    "business_status": "OPERATIONAL",
                }
            ],
            [],
        ]

        url = reverse("restaurants:restaurant-cuisine-match-recommendations")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["recommendation_type"] == "cuisine_match"
        assert data["count"] == 1
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["name"] == "New Italian Place"
        assert data["recommendations"][0]["recommendation_type"] == "cuisine_match"
        assert "matched_cuisines" in data["recommendations"][0]

        # Check user context includes preferred cuisines
        assert "user_context" in data
        assert "preferred_cuisines" in data["user_context"]
        assert len(data["user_context"]["preferred_cuisines"]) > 0

    @pytest.mark.integration
    @patch(
        "apps.restaurants.services.GooglePlacesService.get_recommendations_near_location"
    )
    def test_all_recommendations_endpoint(self, mock_recommendations, setup_user_data):
        """Test the all recommendations API endpoint."""
        client, user = setup_user_data

        # Mock the Google Places response
        mock_recommendations.side_effect = [
            # Good recommendations - first location
            [
                {
                    "place_id": "good1",
                    "name": "Great Place",
                    "rating": 4.5,
                    "vicinity": "Excellent dining",
                    "cuisines": ["Italian Restaurant"],
                    "business_status": "OPERATIONAL",
                }
            ],
            # Good recommendations - second location
            [],
            # Cheap recommendations - first location
            [
                {
                    "place_id": "cheap1",
                    "name": "Budget Place",
                    "rating": 3.5,
                    "price_level": 1,
                    "vicinity": "Affordable",
                    "cuisines": ["Restaurant"],
                    "business_status": "OPERATIONAL",
                }
            ],
            # Cheap recommendations - second location
            [],
            # Cuisine match - first location
            [
                {
                    "place_id": "match1",
                    "name": "Italian Match",
                    "rating": 4.2,
                    "vicinity": "Italian cuisine",
                    "cuisines": ["Italian Restaurant"],
                    "business_status": "OPERATIONAL",
                }
            ],
            # Cuisine match - second location
            [],
        ]

        url = reverse("restaurants:restaurant-all-recommendations")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check all recommendation types are present
        assert "good" in data
        assert "cheap" in data
        assert "cuisine_match" in data
        assert "user_context" in data

        # Check each type has recommendations
        assert len(data["good"]) == 1
        assert len(data["cheap"]) == 1
        assert len(data["cuisine_match"]) == 1

        # Verify recommendation types are correctly set
        assert data["good"][0]["recommendation_type"] == "good"
        assert data["cheap"][0]["recommendation_type"] == "cheap"
        assert data["cuisine_match"][0]["recommendation_type"] == "cuisine_match"

    @pytest.mark.integration
    def test_recommendations_with_limit_parameter(self, setup_user_data):
        """Test recommendations endpoints with limit parameter."""
        client, user = setup_user_data

        with patch(
            "apps.restaurants.services.GooglePlacesService.get_recommendations_near_location"
        ) as mock_rec:
            mock_rec.return_value = []

            # Test with custom limit
            url = reverse("restaurants:restaurant-good-recommendations")
            response = client.get(url, {"limit": 5})

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["count"] == 0  # No recommendations from mock

    @pytest.mark.integration
    def test_recommendations_unauthenticated(self):
        """Test that recommendations require authentication."""
        client = APIClient()  # No authentication

        url = reverse("restaurants:restaurant-good-recommendations")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    def test_recommendations_no_visit_history(self, authenticated_client):
        """Test recommendations when user has no visit history."""
        client, user = authenticated_client

        url = reverse("restaurants:restaurant-good-recommendations")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["recommendation_type"] == "good"
        assert data["count"] == 0
        assert len(data["recommendations"]) == 0

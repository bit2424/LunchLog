"""
URL configuration for restaurants app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"", views.RestaurantViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "restaurants"

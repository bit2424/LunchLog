"""
URL configuration for receipts app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'receipts'

router = DefaultRouter()
router.register(r'', views.ReceiptViewSet, basename='receipts')

urlpatterns = [
    path('', include(router.urls)),
]


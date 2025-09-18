"""
URL configuration for receipts app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
# router.register(r'', views.ReceiptViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

app_name = 'receipts'

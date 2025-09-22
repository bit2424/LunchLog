from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from . import views

app_name = 'users'

urlpatterns = [
    # Session-based authentication
    path('auth/signup/', views.CreateUserView.as_view(), name='signup'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    
    # JWT authentication
    path('auth/jwt/create/', views.CustomTokenObtainPairView.as_view(), name='jwt_create'),
    path('auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt_refresh'),
    path('auth/jwt/verify/', TokenVerifyView.as_view(), name='jwt_verify'),
    
    # User profile
    path('me/', views.CurrentUserView.as_view(), name='current_user'),
]

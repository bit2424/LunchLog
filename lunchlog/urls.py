"""
URL configuration for lunchlog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from argparse import Namespace
import traceback
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from django.shortcuts import render
from django.conf import settings
from django.template.response import TemplateResponse
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response as DRFResponse


schema_view = get_schema_view(
    openapi.Info(
        title="LunchLog API",
        default_version="v1",
        description="""
        LunchLog - Office Lunch Receipt Management and Recommendation System - REST API Backend
        
        ## Features
        - **Receipt Management**: Upload, categorize, and track lunch receipts
        - **Restaurant Database**: Maintain a database of preferred restaurants  
        - **Recommendation System**: Get personalized restaurant recommendations
        - **Authentication**: Multiple auth methods (Session, Token, JWT)
        
        ## Authentication
        This API supports three authentication methods:
        - **Session Authentication**: For web applications
        - **Token Authentication**: For mobile apps and webhooks  
        - **JWT Authentication**: For modern applications
        
        ## Recommendation Endpoints
        The restaurant recommendation system provides:
        - **Good Restaurants**: Highly-rated recommendations near frequent locations
        - **Cheap Restaurants**: Budget-friendly options near frequent locations
        - **Cuisine Match**: Restaurants matching your preferred cuisines
        - **All Recommendations**: Combined view of all recommendation types
        """,
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


def swagger_with_preauth(request, *args, **kwargs):
    """Render Swagger UI with pre-populated Bearer token from default user."""
    token_value = ""
    try:
        User = get_user_model()
        default_email = getattr(settings, "DEFAULT_USER_EMAIL", "basic@example.com")
        user = User.objects.filter(email=default_email).first()
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            token_value = token.key
    except Exception:
        # Fallback if user doesn't exist or token creation fails
        token_value = ""
        print("LunchLog: ❌ Failed to get default user or token")
        print(traceback.format_exc())

    # Get the standard Swagger UI response
    response = schema_view.with_ui("swagger", cache_timeout=0)(request, *args, **kwargs)

    return response


def health_check(request):
    """Simple health check endpoint for ECS health checks."""
    return JsonResponse({
        "status": "healthy",
        "service": "lunchlog-backend"
    })

def default(request):
    """Default endpoint for the root URL."""
    return JsonResponse({
        "status": "ok",
        "message": "LunchLog API is running"
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    # Health check endpoint
    path("health/", health_check, name="health_check"),
    path("", default, name="default"),
    # API Documentation
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^swagger/$",
        schema_view.with_ui('swagger', cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
    # API Endpoints
    path(
        "api/v1/",
        include(
            [
                path("", include(("apps.users.urls", "users"), namespace="users")),
                path("auth/token/", obtain_auth_token, name="api_token_auth"),
                path(
                    "receipts/",
                    include(("apps.receipts.urls", "receipts"), namespace="receipts"),
                ),
                path(
                    "restaurants/",
                    include(
                        ("apps.restaurants.urls", "restaurants"),
                        namespace="restaurants",
                    ),
                ),
            ]
        ),
    ),
]

# Serve media files in development
if settings.DEBUG:
    # Serve app static files via finders without collectstatic in development
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

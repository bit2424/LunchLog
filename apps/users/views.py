from django.contrib.auth import login
from django.conf import settings
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView as SimpleJWTTokenObtainPairView,
    TokenRefreshView as SimpleJWTTokenRefreshView,
    TokenVerifyView as SimpleJWTTokenVerifyView,
)
from .serializers import UserSerializer, AuthTokenSerializer


@method_decorator(csrf_exempt, name="dispatch")
class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system and log them in."""

    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Log the user in
        login(request, user)

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    """Login endpoint that creates a session."""

    serializer_class = AuthTokenSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Create the session
        login(request, user)

        # Return user data
        user_serializer = UserSerializer(user)
        return Response(user_serializer.data)


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """Get or update the current authenticated user's profile."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Return the current authenticated user."""
        return self.request.user


# Custom JWT Views with Swagger Documentation
class TokenObtainPairView(SimpleJWTTokenObtainPairView):
    """
    JWT Token Creation - Obtain access and refresh tokens.

    Use this endpoint to get JWT tokens for authentication. In development,
    you can use the default user credentials provided below.
    """

    @swagger_auto_schema(
        operation_summary="Create JWT Token Pair",
        operation_description="""
        Obtain a new JWT access and refresh token pair by providing valid credentials.
        
        **Development Default User:**
        - Email: `basic@example.com`
        - Password: `basic123`
        
        The access token should be used in the Authorization header as: `Bearer <access_token>`
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="User's email address",
                    example="basic@example.com",
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description="User's password",
                    example="basic123",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="JWT tokens created successfully",
                examples={
                    "application/json": {
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    }
                },
            ),
            401: openapi.Response(
                description="Invalid credentials",
                examples={
                    "application/json": {
                        "detail": "No active account found with the given credentials"
                    }
                },
            ),
        },
        tags=["Authentication"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenRefreshView(SimpleJWTTokenRefreshView):
    """JWT Token Refresh - Get a new access token using refresh token."""

    @swagger_auto_schema(
        operation_summary="Refresh JWT Access Token",
        operation_description="""
        Get a new access token using a valid refresh token.
        This allows you to extend your session without re-authenticating.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Valid refresh token",
                    example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="New access token generated",
                examples={
                    "application/json": {
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                    }
                },
            ),
            401: openapi.Response(
                description="Invalid or expired refresh token",
                examples={
                    "application/json": {
                        "detail": "Token is invalid or expired",
                        "code": "token_not_valid",
                    }
                },
            ),
        },
        tags=["Authentication"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenVerifyView(SimpleJWTTokenVerifyView):
    """JWT Token Verification - Verify if a token is valid."""

    @swagger_auto_schema(
        operation_summary="Verify JWT Token",
        operation_description="""
        Verify that a JWT token is valid and has not expired.
        Useful for checking token validity before making API calls.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["token"],
            properties={
                "token": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="JWT token to verify (access or refresh)",
                    example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Token is valid", examples={"application/json": {}}
            ),
            401: openapi.Response(
                description="Token is invalid or expired",
                examples={
                    "application/json": {
                        "detail": "Token is invalid or expired",
                        "code": "token_not_valid",
                    }
                },
            ),
        },
        tags=["Authentication"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

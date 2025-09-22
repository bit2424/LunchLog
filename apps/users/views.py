from django.contrib.auth import login
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from decouple import config
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer, AuthTokenSerializer


@method_decorator(csrf_exempt, name='dispatch')
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
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """Login endpoint that creates a session."""
    serializer_class = AuthTokenSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
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


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token creation view with default values for Swagger."""
    permission_classes = (AllowAny,)
    
    @swagger_auto_schema(
        operation_description="Create JWT token pair for authentication",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='User email address',
                    default=config('DEFAULT_USER_EMAIL', default='basic@example.com')
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='User password',
                    default=config('DEFAULT_USER_PASSWORD', default='basic123')
                ),
            },
            required=['email', 'password']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access': openapi.Schema(type=openapi.TYPE_STRING, description='Access token (use with Bearer prefix)'),
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
                }
            ),
            401: 'Invalid credentials'
        }
    )
    def post(self, request, *args, **kwargs):
        """Create JWT token pair with enhanced error handling."""
        return super().post(request, *args, **kwargs)

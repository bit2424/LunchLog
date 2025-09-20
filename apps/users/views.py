from django.contrib.auth import login
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
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

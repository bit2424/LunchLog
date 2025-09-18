from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user object."""
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 8}}
    
    def create(self, validated_data):
        """Create a new user with encrypted password and return it."""
        return User.objects.create_user(**validated_data)


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for user authentication object."""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        """Validate and authenticate the user."""
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,  # Django uses username internally
            password=password
        )

        if not user:
            msg = 'Unable to authenticate with provided credentials.'
            raise serializers.ValidationError(msg, code='authentication')

        attrs['user'] = user
        return attrs

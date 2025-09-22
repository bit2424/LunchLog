"""
Custom authentication classes for the lunchlog project.
"""

from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class WebhookTokenAuthentication(TokenAuthentication):
    """
    Token authentication specifically for webhook endpoints.
    Uses a different token model or validation logic if needed.
    """

    keyword = "Bearer"

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)

        if not user.is_active:
            raise AuthenticationFailed("User inactive or deleted.")

        return user, token

"""
Custom permission classes for the lunchlog project.
"""

from rest_framework.permissions import BasePermission


class IsWebhookUser(BasePermission):
    """
    Permission class for webhook endpoints.
    Allows access only to users with specific webhook permissions.
    """

    def has_permission(self, request, view):
        """
        Check if the user has webhook permissions.
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Add webhook-specific permission logic here
        # For example, check if user has 'webhook_access' permission
        # return request.user.has_perm('auth.webhook_access')

        # For now, allow all authenticated users
        return True


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        """
        Read permissions are allowed to any request,
        so we'll always allow GET, HEAD or OPTIONS requests.
        """
        # Read permissions for any request
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # Write permissions only to the owner of the object
        return obj.owner == request.user

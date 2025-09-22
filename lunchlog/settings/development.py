"""
Development settings for lunchlog project.
"""

from .base import *

# Override settings for development
DEBUG = True

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Development-specific apps (uncomment django_extensions after installing)
INSTALLED_APPS += [
    "django_extensions",
]

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Development database (PostgreSQL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "lunchlog",
        "USER": "lunchlog",
        "PASSWORD": "lunchlog123",
        "HOST": config(
            "DB_HOST", default="db"
        ),  # Use 'db' for Docker, 'localhost' otherwise
        "PORT": "5432",
    }
}

# Less restrictive CORS in development
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar (uncomment to enable)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
# INTERNAL_IPS = ['127.0.0.1']

# Disable security features in development
SECURE_SSL_REDIRECT = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

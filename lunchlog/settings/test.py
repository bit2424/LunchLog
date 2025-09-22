"""
Test settings for lunchlog project.
"""

from .base import *

# Use in-memory database for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Password hashers for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging below CRITICAL level to reduce noise
LOGGING_CONFIG = None

# Email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Media files for tests
MEDIA_ROOT = "/tmp/lunchlog_test_media"

# Disable CORS checks in tests
CORS_ALLOW_ALL_ORIGINS = True

# Test-specific settings
DEBUG = False
SECRET_KEY = "test-secret-key-not-for-production"

# Ensure no HTTPS redirects or secure-only cookies during tests
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_PROXY_SSL_HEADER = None

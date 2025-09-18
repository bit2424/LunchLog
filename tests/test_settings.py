"""
Test settings configuration.
"""

import pytest
from django.conf import settings
from django.test import override_settings


class TestSettings:
    """Test Django settings configuration."""

    def test_debug_is_false_in_test(self):
        """Test that DEBUG is False in test environment."""
        assert settings.DEBUG is False

    def test_secret_key_is_set(self):
        """Test that SECRET_KEY is configured."""
        assert settings.SECRET_KEY
        assert len(settings.SECRET_KEY) > 10

    def test_installed_apps_includes_drf(self):
        """Test that DRF is in INSTALLED_APPS."""
        assert 'rest_framework' in settings.INSTALLED_APPS
        assert 'rest_framework.authtoken' in settings.INSTALLED_APPS

    def test_installed_apps_includes_local_apps(self):
        """Test that our local apps are installed."""
        assert 'apps.receipts' in settings.INSTALLED_APPS
        assert 'apps.restaurants' in settings.INSTALLED_APPS

    def test_database_configuration(self):
        """Test database configuration."""
        db_config = settings.DATABASES['default']
        assert db_config['ENGINE'] == 'django.db.backends.sqlite3'
        assert db_config['NAME'] == ':memory:'

    def test_rest_framework_configuration(self):
        """Test REST framework configuration."""
        drf_config = settings.REST_FRAMEWORK
        assert 'rest_framework.authentication.SessionAuthentication' in drf_config['DEFAULT_AUTHENTICATION_CLASSES']
        assert 'rest_framework.authentication.TokenAuthentication' in drf_config['DEFAULT_AUTHENTICATION_CLASSES']

    @override_settings(DEBUG=True)
    def test_settings_override(self):
        """Test that settings can be overridden in tests."""
        assert settings.DEBUG is True

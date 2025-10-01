"""
Unified Django settings for the lunchlog project.

All environments use this single module. Behavior is toggled primarily via the
PROFILE environment variable:
  - PROFILE=prod  → production hardening and overrides
  - any other value (or unset) → development defaults

Environment variables are read via python-decouple's config().
"""

import os
import logging
from datetime import timedelta
from pathlib import Path

from decouple import config
import dj_database_url


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Profile and debug
PROFILE = config("PROFILE", default="dev").strip().lower()
IS_PROD = PROFILE == "prod"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=(not IS_PROD), cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda v: [s.strip() for s in v.split(",")],
)

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "corsheaders",
    "storages",
    "django_celery_beat",
    "drf_yasg",
]

LOCAL_APPS = [
    "apps.users",
    "apps.receipts",
    "apps.restaurants",
]

# Custom user model
AUTH_USER_MODEL = "users.User"

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Development-only apps
if not IS_PROD:
    INSTALLED_APPS += [
        "django_extensions",
    ]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "lunchlog.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "lunchlog.wsgi.application"

# Database
# Prefer DATABASE_URL if provided; otherwise fall back to DB_* or POSTGRES_* variables
DATABASE_URL = config("DATABASE_URL", default=None)

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    }
    DB_USER = DATABASE_URL.split("://")[1].split(":")[0]
    DB_PASSWORD = DATABASE_URL.split("://")[1].split(":")[1].split("@")[0]
    DB_HOST = DATABASE_URL.split("://")[1].split(":")[1].split("@")[1][0]
    DB_PORT = DATABASE_URL.split("://")[1].split(":")[2].split("/")[0]
    DB_NAME = DATABASE_URL.split("://")[1].split(":")[2].split("/")[1]
else:
    DB_NAME = config("DB_NAME", default=config("POSTGRES_DB", default="lunchlog"))
    DB_USER = config("DB_USER", default=config("POSTGRES_USER", default="lunchlog"))
    DB_PASSWORD = config(
        "DB_PASSWORD", default=config("POSTGRES_PASSWORD", default="lunchlog123")
    )
    DB_HOST = config("DB_HOST", default=("db_prod" if IS_PROD else "db"))
    DB_PORT = config("DB_PORT", default="5432")

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": DB_NAME,
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "HOST": DB_HOST,
            "PORT": DB_PORT,
        }
    }

logger = logging.getLogger("django")
logger.info(f"Profile: {PROFILE}")
logger.info(f"Database host: {DATABASES['default']['HOST']}")
logger.info(f"Database port: {DATABASES['default']['PORT']}")

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Minimal static files config (required for Django admin)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# Media files (User uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# AWS S3 Storage Configuration
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default=None)
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default=None)
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default=None)
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_SIGNATURE_VERSION = config("AWS_S3_SIGNATURE_VERSION", default="s3v4")

if AWS_STORAGE_BUCKET_NAME:
    # Use S3 only for media (user uploads). Serve static locally.
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage" if IS_PROD else "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = True
else:
    # Local storage for development and non-S3 setups
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage" if IS_PROD else "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
}

# CORS settings
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=lambda v: [s.strip() for s in v.split(",")],
)
CORS_ALLOW_CREDENTIALS = True

# Swagger/OpenAPI Settings
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Token": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Token-based authentication with format: Token &lt;token&gt;"
        },
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT authentication with format: Bearer &lt;token&gt;"
        }
    },
    "USE_SESSION_AUTH": False,
    "LOGIN_URL": None,  # Disable Django login redirect
    "LOGOUT_URL": None,
    "JSON_EDITOR": True,
    "SUPPORTED_SUBMIT_METHODS": ["get", "post", "put", "delete", "patch"],
    "OPERATIONS_SORTER": "alpha",
    "TAGS_SORTER": "alpha",
    "DOC_EXPANSION": "none",
    "DEEP_LINKING": True,
    "SHOW_EXTENSIONS": True,
    "DEFAULT_MODEL_RENDERING": "model",
    "PERSIST_AUTH": True,
}

# Security baseline
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "SAMEORIGIN"  # Allow same-origin framing for Swagger UI

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

# Simple JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}

# Celery Configuration
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Celery Beat Configuration
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Google Places API Configuration
GOOGLE_PLACES_API_KEY = config("GOOGLE_PLACES_API_KEY", default=None)

if IS_PROD:
    # # Honor HTTPS from proxy/load balancer
    # SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # USE_X_FORWARDED_HOST = True

    # # Enforce HTTPS in production (can be overridden via env)
    # SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    # SESSION_COOKIE_SECURE = True
    # CSRF_COOKIE_SECURE = True

    # # HSTS
    # SECURE_HSTS_SECONDS = 31536000
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True

    # # CORS/CSRF host config for production
    # CORS_ALLOW_ALL_ORIGINS = False
    # CSRF_TRUSTED_ORIGINS = config(
    #     "CSRF_TRUSTED_ORIGINS",
    #     default="",
    #     cast=lambda v: [s.strip() for s in v.split(",")] if v else [],
    # )

    SECURE_SSL_REDIRECT = False
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_TYPE_NOSNIFF = False
    CORS_ALLOW_ALL_ORIGINS = True
    
    # Optional: write logs to file in production
    LOGGING["handlers"]["file"] = {
        "level": "INFO",
        "class": "logging.FileHandler",
        "filename": "/var/log/lunchlog/django.log",
        "formatter": "verbose",
    }
    LOGGING["loggers"]["django"]["handlers"].append("file")
    LOGGING["loggers"]["apps"]["handlers"].append("file")
else:
    # Development conveniences
    SECURE_SSL_REDIRECT = False
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_TYPE_NOSNIFF = False
    CORS_ALLOW_ALL_ORIGINS = True



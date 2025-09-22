"""
ASGI config for lunchlog project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

profile = os.environ.get("PROFILE", "dev").strip().lower()
default_settings = (
    "lunchlog.settings.production"
    if profile == "prod"
    else "lunchlog.settings.development"
)
os.environ["DJANGO_SETTINGS_MODULE"] = default_settings

application = get_asgi_application()

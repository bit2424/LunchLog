"""
WSGI config for lunchlog project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

profile = os.environ.get('PROFILE', 'dev').strip().lower()
default_settings = 'lunchlog.settings.production' if profile == 'prod' else 'lunchlog.settings.development'
# Force the settings module based on PROFILE to avoid accidental HTTPS redirects in dev
os.environ['DJANGO_SETTINGS_MODULE'] = default_settings

application = get_wsgi_application()

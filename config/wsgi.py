"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import environ

from django.core.wsgi import get_wsgi_application

env = environ.Env()
environ.Env.read_env()

settings_module = env('DJANGO_SETTINGS_MODULE', default='config.settings.dev')

if settings_module is None or isinstance(settings_module, bytes):
    settings_module = 'config.settings.dev'
elif isinstance(settings_module, str):
    pass
else:
    settings_module = 'config.settings.dev'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

application = get_wsgi_application()

print("wsgi", settings_module)

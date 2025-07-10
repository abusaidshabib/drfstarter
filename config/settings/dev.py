from .base import *

# Development settings
DEBUG = True

# Add debug toolbar for development
INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]

INSTALLED_APPS += ["debug_toolbar"]
INSTALLED_APPS += ["django_extensions"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

# Internal IPs for debug toolbar
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    },
}

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Relax CORS for development
CORS_ALLOW_ALL_ORIGINS = True

CELERY_TASK_EAGER_PROPAGATES = True

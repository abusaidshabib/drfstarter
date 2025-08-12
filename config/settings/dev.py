from .base import *

# Development settings
DEBUG = True

# Add debug toolbar for development
INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]

INSTALLED_APPS += ["debug_toolbar"]
INSTALLED_APPS += ["django_extensions"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

# Internal IPs for debug toolbar
ALLOWED_HOSTS = ["*"]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    },
}

# SECURITY
SESSION_COOKIE_ACCESS_TOKEN_MAX_AGE = 3600
SESSION_COOKIE_REFRESH_TOKEN_MAX_AGE = 1296000
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_AGE = 1209600

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'
X_FRAME_OPTIONS = "SAMEORIGIN"

FRONTEND_BASE_URL = env("FRONTEND_BASE_URL")


# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Relax CORS for development
CORS_ALLOW_ALL_ORIGINS = True

CELERY_TASK_EAGER_PROPAGATES = True

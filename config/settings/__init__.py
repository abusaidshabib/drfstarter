import environ
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent

env = environ.Env()
env.read_env(BASE_DIR / ".env")

DJANGO_ENV = env("DJANGO_ENV")
print("i'm working fine", DJANGO_ENV)

if DJANGO_ENV == "production":
    from .prod import *
elif DJANGO_ENV == "development":
    from .dev import *
else:
    raise ImproperlyConfigured(
        "DJANGO_ENV must be set to 'development' or 'production'")

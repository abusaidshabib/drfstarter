import os
import environ

from django.core.asgi import get_asgi_application

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

application = get_asgi_application()


print("asgi",settings_module)

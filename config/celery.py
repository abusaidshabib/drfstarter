import os
import environ

from celery import Celery

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

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')


app.autodiscover_tasks()

print("asgi", settings_module)

from django.urls import path
from django.contrib import admin
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
]

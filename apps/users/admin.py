from django.contrib import admin
from apps.users.models import MyUser


@admin.register(MyUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username",)

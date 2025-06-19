from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from apps.core.models import BaseModel
from apps.users.managers import MyUserManager

# Register your models here.


class MyUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(max_length=30, null=False, blank=False)
    date_joined = models.DateTimeField(
        verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    sensor_update_permission = models.BooleanField(default=False)
    profile_picture = models.ImageField(
        upload_to="profile_picture/%Y/%m/", null=True, blank=True, default=None)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = MyUserManager()

    def __str__(self) -> str:
        return f"User {self.email}"

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return True

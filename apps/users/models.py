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


class RequestAuditLog(models.Model):
    user = models.ForeignKey(
        MyUser, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='audit_logs', verbose_name="User"
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="IP Address"
    )
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    path = models.TextField(verbose_name="Path")
    method = models.CharField(max_length=10, verbose_name="Method")
    timestamp = models.DateTimeField(
        auto_now_add=True, verbose_name="Timestamp")
    status_code = models.IntegerField(
        null=True, blank=True, verbose_name="Status Code")

    def __str__(self):
        return f"{self.user.email if self.user else 'Anonymous'} - {self.method} {self.path} ({self.status_code})"

    class Meta:
        verbose_name = "Request Audit Log"
        verbose_name_plural = "Request Audit Logs"
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]

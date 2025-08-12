# pylint: disable=import-error
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.users.managers import MyUserManager

type_choices = [
    ("free", "free"),
    ("paid", "paid"),
    ("depends", "depends")
]

type_required = [
    ("sensor", "sensor"),
    ("camera", "camera")
]

# camera_update


class AppFeature(BaseModel):
    name = models.CharField(max_length=250,
                            verbose_name="Feature Name")
    tag = models.CharField(max_length=255, unique=True)
    order = models.IntegerField(default=0)
    description = models.TextField(
        blank=True, null=True, verbose_name="Description")
    icon = models.ImageField(upload_to='feature_icons/',
                             blank=True, null=True, verbose_name="Feature Icon")
    price = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0)]
    )
    requirements = models.TextField(
        blank=True, null=True, verbose_name="requirements")
    required = models.CharField(
        max_length=255, choices=type_required, null=True, blank=True, verbose_name="required")
    feature_type = models.CharField(
        max_length=255, choices=type_choices, default="paid")
    w = models.IntegerField(default=4, verbose_name="Width")
    h = models.IntegerField(default=65, verbose_name="Height")
    x = models.IntegerField(blank=True, null=True,
                            verbose_name="X Position", default=None)
    y = models.IntegerField(blank=True, null=True,
                            verbose_name="Y Position", default=None)

    def __str__(self) -> str:
        return self.name

    def clean(self):
        if not self.name.strip():
            raise ValidationError(
                "Feature name cannot be blank or whitespace only.")

    class Meta:
        verbose_name = "App Feature"
        verbose_name_plural = "App Features"


class Company(BaseModel):
    name = models.CharField(max_length=250, unique=True,
                            verbose_name="Company Name")
    name_ar = models.CharField(max_length=250, unique=True,
                               verbose_name="Company Arabic Name", default=None, null=True, blank=True)
    subdomain = models.CharField(
        max_length=250, unique=True, verbose_name="Subdomain")
    logo = models.ImageField(
        upload_to='company_logo/%Y/', blank=True, null=True, verbose_name="Logo")
    fav_icon = models.ImageField(
        upload_to='company_logo/%Y/', blank=True, null=True, verbose_name="Favicon")
    created_by = models.ForeignKey(
        'MyUser', related_name='companies_created', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Created By")
    updated_by = models.ForeignKey(
        'MyUser', related_name='companies_updated', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Updated By")
    address = models.TextField(verbose_name="Address", blank=True, null=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"


class CompanyOTP(models.Model):
    token = models.CharField(max_length=64, unique=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP: {self.token} | Used: {self.used}"


class Branch(BaseModel):
    company = models.ForeignKey(
        Company, related_name='branches', on_delete=models.CASCADE, verbose_name="Company")
    created_by = models.ForeignKey(
        'MyUser', related_name='branches', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Created By")
    name = models.CharField(max_length=250, verbose_name="Branch Name")
    location = models.TextField(verbose_name="Location", null=True, blank=True)
    features = models.ManyToManyField(
        'AppFeature', related_name='branches', verbose_name=_("Features"))

    def __str__(self) -> str:
        return f"ID: {self.id}, company: {self.company.name}, branch: {self.name}"

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name'], name='unique_branch_per_company')
        ]


class Contact(BaseModel):
    company = models.ForeignKey(
        Company, on_delete=models.SET_NULL, related_name='contacts', verbose_name="Company", null=True, blank=True)
    branch = models.ForeignKey(
        Branch, on_delete=models.SET_NULL, related_name='contacts', verbose_name="Branch", null=True, blank=True)
    email = models.EmailField(max_length=60, unique=True, verbose_name="Email")
    phone_number = models.CharField(
        max_length=20, unique=True, verbose_name="Phone Number")

    def __str__(self) -> str:
        return f"{self.company}"

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"


class MyUser(AbstractBaseUser, PermissionsMixin, BaseModel):
    company = models.ForeignKey(
        Company, related_name='users', on_delete=models.SET_NULL, verbose_name="Company", null=True, blank=True)
    assigned_branches = models.ManyToManyField(
        Branch,
        related_name='users',
        verbose_name="Assigned Branches",
        blank=True,
        default=None
    )
    email = models.EmailField(max_length=60, unique=True, verbose_name="Email")
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False, verbose_name="Verified")
    name = models.CharField(max_length=250, verbose_name="Name")
    name_ar = models.CharField(
        max_length=250, verbose_name="Arabic Name", null=True, blank=True)
    date_joined = models.DateTimeField(
        verbose_name="Date Joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="Last Login", auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    is_superuser = models.BooleanField(default=False, verbose_name="Superuser")
    is_owner = models.BooleanField(
        default=False, verbose_name="Company Owner")
    is_admin = models.BooleanField(default=False, verbose_name="Admin")
    is_staff = models.BooleanField(default=False, verbose_name="Staff")
    is_two_step = models.BooleanField(
        default=False, verbose_name="Two-Step Verification")

    token_valid = models.BooleanField(
        default=False, verbose_name="Token Valid")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "name_ar"]
    company_create = models.BooleanField(
        default=False, verbose_name="Company Create Permission")
    branch_create = models.BooleanField(
        default=False, verbose_name="Branch Create Permission")

    objects = MyUserManager()

    def __str__(self) -> str:
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return True

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class UserBranchLayout(BaseModel):
    user = models.ForeignKey(
        MyUser, on_delete=models.CASCADE, related_name='user_branch_layout', verbose_name="User")
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name='user_branch_layout', verbose_name="Branch", null=True, blank=True)
    position = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'branch'], name='unique_user_branch_layout')
        ]


class UserBranchFeatures(BaseModel):
    user = models.ForeignKey(
        MyUser, on_delete=models.CASCADE, related_name='user_branch_features', verbose_name="User")
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name='user_branch_features', verbose_name="Branch", null=True, blank=True)
    features = models.ManyToManyField(
        AppFeature, related_name='user_branch_features', verbose_name="Features", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'branch'], name='unique_user_branch_features')
        ]


class MyUserDetails(BaseModel):
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    user = models.OneToOneField(
        MyUser, on_delete=models.CASCADE, related_name='user_details', verbose_name="User")
    address = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Address")
    phone_number = models.CharField(
        max_length=20, null=True, blank=True, verbose_name="Phone Number")
    date_of_birth = models.DateField(
        null=True, blank=True, verbose_name="Date of Birth")
    profile_picture = models.ImageField(
        upload_to="user_profile_pictures/%Y/%m/", null=True, blank=True, default=None, verbose_name="Profile Picture")
    user_signature = models.ImageField(
        upload_to="user_signatures/%Y/%m/", null=True, blank=True, default=None, verbose_name="User Signature")
    blood_group = models.CharField(
        max_length=3, choices=BLOOD_GROUP_CHOICES, null=True, blank=True, verbose_name="Blood Group")
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, null=True, blank=True, verbose_name="Gender")

    def __str__(self) -> str:
        return f"Details for {self.user.email}"

    class Meta:
        verbose_name = "User Detail"
        verbose_name_plural = "User Details"


class Subscription(BaseModel):
    features = models.ManyToManyField(
        AppFeature, related_name='subscriptions', verbose_name="Features")
    package_name = models.CharField(
        max_length=250, unique=True, verbose_name="Package Name")
    package_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Price")

    def __str__(self) -> str:
        return self.package_name

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"


class SubscriptionHistory(BaseModel):
    REGISTRATION_STEPS = [
        ('features_selected', 'Features Selected'),
        ('token_verified', 'Token Verified'),
        ('company_created', 'Company Created'),
        ('completed', 'Completed'),
    ]
    uid = models.CharField(default=None, null=True, blank=True)
    user = models.ForeignKey(
        MyUser, on_delete=models.CASCADE, related_name='subscription_history', verbose_name="User")
    company = models.ForeignKey(
        Company, on_delete=models.SET_NULL, related_name='subscription_history', verbose_name="Company", null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL,
                               related_name='subscription_history', verbose_name="Branch", null=True, blank=True)
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, related_name='subscription_histories',
        null=True, blank=True, verbose_name="Subscription"
    )
    start_date = models.DateTimeField(
        auto_now_add=True, verbose_name="Start Date")
    end_date = models.DateTimeField(
        null=True, blank=True, verbose_name="End Date")
    package_duration = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Duration (month)")
    features = models.ManyToManyField(
        AppFeature, related_name='subscription_history', verbose_name="Features", blank=True)
    paid = models.BooleanField(default=False, verbose_name="Paid")
    payment = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Price")
    is_active = models.BooleanField(default=False, verbose_name="Active")
    activate_by = models.ForeignKey(
        MyUser, on_delete=models.CASCADE, related_name='activated_subscriptions', verbose_name="Activated By", default=None, null=True, blank=True)

    registration_step = models.CharField(
        max_length=20, choices=REGISTRATION_STEPS, default='features_selected', verbose_name="Registration Step")

    def __str__(self) -> str:
        return f"{self.paid}"

    class Meta:
        verbose_name = "Subscription History"
        verbose_name_plural = "Subscription Histories"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'company', 'subscription', 'start_date'],
                name='unique_subscription_history'
            )
        ]


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

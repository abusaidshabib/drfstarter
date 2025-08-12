from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import (AppFeature, Branch, Company, CompanyOTP,
                               Contact, MyUser, MyUserDetails, RequestAuditLog,
                               Subscription, SubscriptionHistory,
                               UserBranchFeatures, UserBranchLayout)


@admin.register(AppFeature)
class AppFeatureAdmin(admin.ModelAdmin):
    list_display = ("id", "tag", "description",
                    "price", "feature_type", "required")
    list_filter = ("feature_type", "required")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "package_price", "package_name")


@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "company",
                    "start_date", "end_date", "is_active", "registration_step")


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "subdomain",
                    "logo", "fav_icon", "created_by")


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "company",
                    "location", "created_by")
    list_filter = ("company",)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("email", "company", "phone_number")


class MyUserDetailsInline(admin.StackedInline):
    model = MyUserDetails
    can_delete = False
    verbose_name_plural = 'User Details'
    fk_name = 'user'


class UserBranchLayoutInline(admin.TabularInline):
    model = UserBranchLayout
    extra = 0
    verbose_name_plural = 'Branch Layouts'
    fk_name = 'user'


class UserBranchFeaturesInline(admin.TabularInline):
    model = UserBranchFeatures
    extra = 0
    verbose_name_plural = 'Branch Features'
    fk_name = 'user'
    filter_horizontal = ('features',)  # ManyToMany field support


@admin.register(MyUser)
class MyUserAdmin(BaseUserAdmin):
    inlines = [MyUserDetailsInline,
               UserBranchLayoutInline, UserBranchFeaturesInline]

    list_display = ('id', 'email', 'name', 'is_active', 'is_superuser',
                    'company', 'is_admin', 'is_owner', 'token_valid')
    list_filter = ('is_active', 'is_superuser',
                   'is_admin', 'is_owner', 'company')
    search_fields = ('email', 'name')
    ordering = ('-date_joined',)
    filter_horizontal = ('assigned_branches',)
    readonly_fields = ('date_joined', 'last_login')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
         'fields': ('name', 'name_ar', 'company', 'assigned_branches')}),
        ('Permissions', {'fields': ('is_active', 'is_superuser',
         'is_staff', 'is_admin', 'is_owner', 'token_valid')}),
        ('Security', {
         'fields': ('otp', 'otp_created_at', 'is_verified', 'is_two_step')}),
        ('Date Info', {'fields': ('last_login', 'date_joined')}),
        ('Custom Permissions', {
         'fields': ('company_create', 'branch_create')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'name_ar', 'password1', 'password2', 'company'),
        }),
    )


@admin.register(MyUserDetails)
class MyUserDetailsAdmin(admin.ModelAdmin):
    list_display = ("user", "address", "phone_number",
                    "date_of_birth", "user_signature", "blood_group", "gender",)


@admin.register(CompanyOTP)
class CompanyOTPAdmin(admin.ModelAdmin):
    list_display = ('id', 'token', 'used')


@admin.register(RequestAuditLog)
class RequestAuditAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "user_agent", "path",
                    "method", "timestamp", "status_code")


@admin.register(UserBranchLayout)
class UserBranchLayoutAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "branch", "position")
    list_filter = ("user", "branch")


@admin.register(UserBranchFeatures)
class UserBranchFeaturesAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "branch")
    list_filter = ("user", "branch")

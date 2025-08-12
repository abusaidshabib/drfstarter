import json
import random
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.core.utils import (send_custom_email,
                             user_branches_company, generate_unique_token)
from apps.core.utils.position_json import (position_make_json)
from apps.users.models import (AppFeature, Branch, Company, Contact, MyUser,
                               MyUserDetails, Subscription,
                               SubscriptionHistory, UserBranchFeatures,
                               UserBranchLayout)


class AppFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppFeature
        fields = ['id', 'name', 'tag', 'description', 'price', 'requirements']


class UserBranchLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBranchLayout
        fields = ['position']


class ContactInfoSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = serializers.CharField()


class CompanySerializer(serializers.ModelSerializer):
    config = serializers.JSONField(required=False)
    updated_by_email = serializers.CharField(
        source='updated_by.email', read_only=True)
    contact_info = serializers.JSONField(required=False)
    branch_location = serializers.CharField(required=False)
    created_branch_id = serializers.IntegerField(read_only=True)
    subscription_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Company
        fields = ['id', 'name', 'subdomain', 'logo', 'name_ar',
                  'fav_icon', 'created_by', 'config', 'updated_by_email', 'contact_info', 'branch_location', 'created_branch_id', 'subscription_id']
        read_only_fields = ['id', 'updated_by_email', 'created_by']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        created_branch = getattr(self, '_created_branch', None)
        if created_branch:
            representation['created_branch_id'] = created_branch.id
        return representation

    def get_logo(self, obj):
        request = self.context.get('request')
        if obj.logo and hasattr(obj.logo, 'url'):
            return request.build_absolute_uri(obj.logo.url)
        return None

    def get_fav_icon(self, obj):
        request = self.context.get('request')
        if obj.fav_icon and hasattr(obj.fav_icon, 'url'):
            return request.build_absolute_uri(obj.fav_icon.url)
        return None

    def validate(self, attrs):
        request = self.context['request']
        user = self.context['request'].user

        name = attrs.get('name')
        if name and Company.objects.filter(name=name).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError(
                f"A company with the name '{name}' already exists.")

        if not user.company_create and request.method == 'POST':
            raise serializers.ValidationError("Please validate your token")

        contact_info = attrs.get('contact_info')
        if contact_info is not None and not isinstance(contact_info, list):
            raise serializers.ValidationError({
                'contact_info': "This field must be a list."
            })
        subscription_history_id = attrs.get('subscription_id')
        print(subscription_history_id)
        if subscription_history_id:
            try:
                SubscriptionHistory.objects.get(
                    id=subscription_history_id, user=user)
            except SubscriptionHistory.DoesNotExist:
                raise serializers.ValidationError(
                    "Invalid subscription history ID or you do not have permission to access it.")

        return super().validate(attrs)

    def create(self, validated_data):
        user = self.context['request'].user
        config = validated_data.pop('config', None)
        contact_info = validated_data.pop('contact_info', [])
        location = validated_data.pop('branch_location', None)
        subscription_history_id = validated_data.pop('subscription_id', None)

        if user.company:
            raise serializers.ValidationError("You already a company")

        with transaction.atomic():
            company = Company.objects.create(created_by=user, **validated_data)

            if config:
                Theme.objects.create(
                    company=company,
                    config=config
                )

            branch = Branch.objects.create(created_by=user,
                                           name="main_branch",
                                           location=location,
                                           company=company)

            if contact_info:
                for i in contact_info:
                    if i:
                        email = i['email']
                        phone_number = i['phone_number']

                        contact, created = Contact.objects.get_or_create(
                            email=email,
                            defaults={
                                'company': company,
                                'branch': branch,
                                'phone_number': phone_number
                            }
                        )
                        if not created:
                            raise serializers.ValidationError(
                                f"Contact with email '{email}' already exists."
                            )

            subscription_history = SubscriptionHistory.objects.get(
                id=subscription_history_id)

            if subscription_history and subscription_history.company is None:
                subscription_history.company = company
                subscription_history.branch = branch
                subscription_history.start_date = now().date()
                subscription_history.end_date = now().date(
                ) + relativedelta(months=subscription_history.package_duration)
                subscription_history.save()

            if subscription_history:
                branch.features.set(subscription_history.features.all())

            self._created_branch = branch

            user.company_create = False
            user.company = company
            user.is_owner = True
            user.is_admin = True
            user.token_valid = False
            user.save()

            # Get mandatory features for owner
            # 1. Load all free features (always available)
            free_features = AppFeature.objects.filter(feature_type='free')

            # 2. Load features from the user's subscription (if any)
            subscribed_features = (
                subscription_history.features.all()
                if subscription_history
                else AppFeature.objects.none()
            )

            # 3. If any subscribed feature requires a camera, include camera-related dependent features
            if subscribed_features.filter(required='camera').exists():
                camera_related_features = AppFeature.objects.filter(
                    tag__startswith='camera_')
                subscribed_features = subscribed_features | camera_related_features

            # 4. Merge and remove duplicates
            available_features = (
                free_features | subscribed_features).distinct()

            # User features create or update for owner
            user_branch_features, created = UserBranchFeatures.objects.update_or_create(
                user=user,
                branch=branch,
            )

            # Set the many-to-many field (after creating or updating the object)
            user_branch_features.features.set(available_features)

            # Store the user layout position
            position_json = position_make_json(
                subscription_history.features.all(), positions=None)

            layout_obj, created = UserBranchLayout.objects.update_or_create(
                user=user,
                branch=branch,
                defaults={'position': position_json}
            )

            # Register step
            subscription = SubscriptionHistory.objects.get(
                id=subscription_history_id)
            subscription.registration_step = 'completed'
            subscription.save()

        return company

    def update(self, instance, validated_data):
        user = self.context['request'].user
        config = validated_data.pop('config', None)
        contact_info = validated_data.pop('contact_info', None)

        with transaction.atomic():
            # Update Company fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.updated_by = user
            instance.save()

            # Update or create Theme config
            if config is not None:
                Theme.objects.update_or_create(
                    company=instance,
                    defaults={'config': config}
                )

            if contact_info:
                Contact.objects.filter(
                    company=instance, branch=instance).delete()
                for i in contact_info:
                    contact, created = Contact.objects.update_or_create(
                        email=i['email'],
                        defaults={
                            'company': user.company,
                            'branch': instance,
                            'phone_number': i['phone_number']
                        }
                    )

        return instance


class BranchSerializer(serializers.ModelSerializer):
    contact_info = serializers.JSONField(required=False)
    contact_details = serializers.SerializerMethodField()
    subscription_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Branch
        fields = ['id', 'name', 'contact_info', 'contact_details',
                  'location', 'created_by', 'subscription_id']
        read_only_fields = ['created_by']

    def get_contact_details(self, obj):
        contacts = Contact.objects.filter(branch=obj)

        return [
            {
                "email": c.email,
                "phone_number": c.phone_number
            }
            for c in contacts
        ]

    def validate(self, attrs):
        request = self.context['request']
        user = request.user

        name = attrs.get('name')
        if name and Branch.objects.filter(name=name, company=user.company).exists():
            raise serializers.ValidationError(
                f"A branch with the name '{name}' already exists."
            )

        if not user.branch_create and request.method == 'POST':
            raise serializers.ValidationError(
                "Please validate your toke to create branch")

        contact_info = attrs.get('contact_info')
        if contact_info is not None and not isinstance(contact_info, list):
            raise serializers.ValidationError({
                'contact_info': "This field must be a list."
            })

        subscription_id = attrs.get('subscription_id')
        if subscription_id:
            try:
                SubscriptionHistory.objects.get(id=subscription_id, user=user)
            except SubscriptionHistory.DoesNotExist:
                raise serializers.ValidationError(
                    "Invalid subscription history ID or you do not have permission to access it.")

        return super().validate(attrs)

    def create(self, validated_data):
        print("Creating branch with data:", validated_data)
        user = self.context['request'].user
        contact_info = validated_data.pop('contact_info', [])
        subscription_id = validated_data.pop('subscription_id', None)

        with transaction.atomic():
            branch = Branch.objects.create(
                created_by=user, company=user.company, **validated_data)

            subscription_history = SubscriptionHistory.objects.get(
                id=subscription_id)

            subscription_history.company = user.company
            subscription_history.branch = branch
            subscription_history.start_date = now().date()
            subscription_history.end_date = now().date(
            ) + relativedelta(months=subscription_history.package_duration)
            branch.features.set(subscription_history.features.all())
            subscription_history.save()

            if contact_info:
                for i in contact_info:
                    if i:
                        email = i['email']
                        phone_number = i['phone_number']

                        if not email and not phone_number:
                            continue

                        contact, created = Contact.objects.get_or_create(
                            email=email,
                            defaults={
                                'company': user.company,
                                'branch': branch,
                                'phone_number': phone_number
                            }
                        )

                        if not created:
                            raise serializers.ValidationError(
                                f"Contact with email '{email}' already exists."
                            )

            user.branch_create = False
            user.token_valid = False
            user.save()

            # Get mandatory features for owner
            # 1. Load all free features (always available)
            free_features = AppFeature.objects.filter(feature_type='free')
            # 2. Load features from the user's subscription (if any)
            subscribed_features = (
                subscription_history.features.all()
                if subscription_history
                else AppFeature.objects.none()
            )
            # 3. If any subscribed feature requires a camera, include camera-related dependent features
            if subscribed_features.filter(required='camera').exists():
                camera_related_features = AppFeature.objects.filter(
                    tag__startswith='camera_')
                subscribed_features = subscribed_features | camera_related_features
            # 4. Merge and remove duplicates
            available_features = (
                free_features | subscribed_features).distinct()
            # User features create or update for owner
            user_branch_features, created = UserBranchFeatures.objects.update_or_create(
                user=user,
                branch=branch,
            )
            # Set the many-to-many field (after creating or updating the object)
            user_branch_features.features.set(available_features)
            # Store the user layout position
            position_json = position_make_json(
                subscription_history.features.all(), positions=None)

            layout_obj, created = UserBranchLayout.objects.update_or_create(
                user=user,
                branch=branch,
                defaults={'position': position_json}
            )

            if subscription_id:
                print(f"Updating subscription with ID: {subscription_id}")
                subscription = SubscriptionHistory.objects.get(
                    id=subscription_id)
                subscription.registration_step = 'completed'
                subscription.save()

        return branch

    def update(self, instance, validated_data):
        contact_info = validated_data.pop('contact_info', None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            company = instance.company

            if contact_info:
                Contact.objects.filter(
                    company=company, branch=instance).delete()
                for i in contact_info:
                    contact, created = Contact.objects.update_or_create(
                        email=i['email'],
                        defaults={
                            'company': company,
                            'branch': instance,
                            'phone_number': i['phone_number']
                        }
                    )

        return instance


class ResetPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                "New password and confirm password do not match.")
        return attrs


class MyUserSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        required=False
    )
    address = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    user_signature = serializers.ImageField(required=False, allow_null=True)
    blood_group = serializers.ChoiceField(
        choices=MyUserDetails.BLOOD_GROUP_CHOICES, required=False)
    gender = serializers.ChoiceField(
        choices=MyUserDetails.GENDER_CHOICES, required=False
    )

    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    features_branch_input = serializers.CharField(
        required=False, allow_blank=True
    )

    class Meta:
        model = MyUser
        fields = [
            'id',
            'email',
            'name',
            'name_ar',
            'company',
            'branches',
            'is_staff',
            'is_owner',
            'is_admin',
            'is_superuser',
            'is_verified',
            'is_two_step',
            'date_joined',
            'last_login',
            'password',
            'confirm_password',
            'features_branch_input',

            # Flattened fields from MyUserDetails
            'address',
            'phone_number',
            'date_of_birth',
            'profile_picture',
            'user_signature',
            'blood_group',
            'gender',
        ]
        read_only_fields = ['date_joined',
                            'last_login', 'is_superuser', 'is_owner']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        details = getattr(instance, 'user_details', None)
        data['company'] = CompanySerializer(
            instance.company, context=self.context).data if instance.company else None

        def absolute_uri_or_none(file_field):
            if file_field:
                if request:
                    return request.build_absolute_uri(file_field.url)
                return file_field.url  # fallback to relative path
            return None

        if details:
            data.update({
                'address': details.address,
                'phone_number': details.phone_number,
                'date_of_birth': details.date_of_birth,
                'profile_picture': absolute_uri_or_none(details.profile_picture) if details.profile_picture else None,
                'user_signature': absolute_uri_or_none(details.user_signature) if details.user_signature else None,
                'blood_group': details.blood_group,
                'gender': details.gender,
            })
        else:
            data.update({
                'address': None,
                'phone_number': None,
                'date_of_birth': None,
                'profile_picture': None,
                'user_signature': None,
                'blood_group': None,
                'gender': None,
            })

        try:
            _, _, branches = user_branches_company(request)
            data['branches'] = BranchSerializer(
                branches, many=True, context=self.context).data
        except Exception as e:
            data['branches'] = []

        return data

    def validate(self, data):

        request = self.context.get('request')
        if not data.get('company') and hasattr(request.user, 'company'):
            data['company'] = request.user.company

        features_branch_input = data.pop('features_branch_input', None)
        features_branch_input_json = []
        if features_branch_input:
            features_branch_input_json = json.loads(features_branch_input)
            if not isinstance(features_branch_input_json, list):
                raise serializers.ValidationError({
                    'features_branch_input': "This field must be a list."
                })
            branch_ids = [
                item['branch_id']
                for item in features_branch_input_json
                if 'branch_id' in item
            ]

            branches = Branch.objects.filter(id__in=branch_ids)
            if len(branches) != len(branch_ids):
                raise serializers.ValidationError(
                    "One or more branch IDs are invalid.")
            data['assigned_branches'] = branches

        data['features_branch_data'] = features_branch_input_json

        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password or confirm_password:
            if password != confirm_password:
                raise serializers.ValidationError("Passwords do not match.")

            try:
                validate_password(password, None)
            except DjangoValidationError as e:
                raise DRFValidationError({'password': list(e.messages)})

        return data

    def create(self, validated_data):
        features_branch_data = validated_data.pop('features_branch_data', [])
        password = validated_data.pop('password')
        validated_data.pop('confirm_password', None)
        req_user = self.context.get('request').user

        if req_user.is_staff and (not req_user.is_owner or not req_user.is_admin):
            validated_data.pop('is_admin', None)

        detail_fields = {
            'address', 'phone_number', 'date_of_birth', 'profile_picture',
            'user_signature', 'blood_group', 'gender'
        }
        details_data = {key: validated_data.pop(
            key) for key in detail_fields if key in validated_data}
        branch_ins = validated_data.pop('assigned_branches', [])
        validated_data.pop('branches', None)

        user = MyUser.objects.create(**validated_data)

        user.set_password(password)
        user.is_active = True
        user.save()

        if branch_ins:
            user.assigned_branches.set(branch_ins)

        if details_data:
            MyUserDetails.objects.create(user=user, **details_data)

        for item in features_branch_data:
            branch_id = item.get('branch_id')
            feature_ids = item.get('features', [])

            if not branch_id or not isinstance(feature_ids, list):
                continue  # skip invalid items

            try:
                branch = Branch.objects.get(id=branch_id)
                features = AppFeature.objects.filter(id__in=feature_ids)
            except Branch.DoesNotExist:
                raise serializers.ValidationError("Invalid branch ID.")
            except AppFeature.DoesNotExist:
                raise serializers.ValidationError(
                    "One or more feature IDs are invalid.")

            # create or update the UserBranchFeatures
            user_branch_feature, created = UserBranchFeatures.objects.get_or_create(
                user=user,
                branch=branch
            )

            # Set the features for this user-branch relationship
            user_branch_feature.features.set(features)

            position_json = position_make_json(
                features, positions=None)  # Ensure position is created

            UserBranchLayout.objects.update_or_create(
                user=user,
                branch=branch,
                defaults={'position': position_json}
            )

        return user

    def update(self, instance, validated_data):
        request = self.context.get('request')
        features_branch_data = validated_data.pop('features_branch_data', None)

        if 'email' in validated_data and validated_data['email'] != instance.email:
            raise serializers.ValidationError(
                {"email": "Email address cannot be updated."})

        if request and request.user.id == instance.id:
            if 'assigned_branches' in validated_data:
                raise serializers.ValidationError({
                    "assigned_branches_input": "You cannot update your own assigned branches."
                })
            if 'features' in validated_data:
                raise serializers.ValidationError({
                    "features_input": "You cannot update your own features."
                })

        detail_fields = {
            'address', 'phone_number', 'date_of_birth', 'profile_picture',
            'user_signature', 'blood_group', 'gender'
        }

        details_data = {key: validated_data.pop(
            key) for key in detail_fields if key in validated_data}
        branches = validated_data.pop('assigned_branches', None)

        # Update core MyUser fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        password = validated_data.pop('password', None)
        confirm_password = validated_data.pop('confirm_password', None)

        if password and confirm_password:
            if password != confirm_password:
                raise serializers.ValidationError(
                    "Passwords do not match.")
            instance.set_password(password)
        instance.save()

        # Update M2M branches if provided
        if branches is not None:
            instance.assigned_branches.set(branches)

        # Update or create MyUserDetails
        details_instance, _ = MyUserDetails.objects.get_or_create(
            user=instance)
        for attr, value in details_data.items():
            setattr(details_instance, attr, value)
        details_instance.save()

        # 🔄 Update UserBranchFeatures
        if features_branch_data is not None:
            # Clear old mappings first to prevent duplicates (optional)
            UserBranchFeatures.objects.filter(user=instance).delete()

            for item in features_branch_data:
                branch_id = item.get('branch_id')
                feature_ids = item.get('features', [])

                if not branch_id or not isinstance(feature_ids, list):
                    continue

                try:
                    branch = Branch.objects.get(id=branch_id)
                    features = AppFeature.objects.filter(id__in=feature_ids)
                except Branch.DoesNotExist:
                    continue

                user_branch_feature = UserBranchFeatures.objects.create(
                    user=instance,
                    branch=branch
                )
                user_branch_feature.features.set(features)

        return instance


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = MyUser
        fields = ['name', 'email', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'confirm_password': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError(
                {"password": "Passwords do not match."})
        validate_password(attrs['password'])
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password')
        user = MyUser(**validated_data)
        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.set_password(password)

        try:
            user.save()
            # raise inside this if email fails
            send_custom_email(user, {'otp': otp}, "signup_otp")
        except Exception as e:
            # Any exception (e.g., SMTP failure) will roll back the transaction
            raise serializers.ValidationError(
                {"email": f"Could not send OTP: {str(e)}"})

        return user


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        otp = attrs.get('otp')
        email = attrs.get('email')
        user = MyUser.objects.get(email=email)

        if not user or not user.is_authenticated:
            raise serializers.ValidationError(
                {"user": "Authentication required."})

        if user.otp != otp:
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        # Check OTP expiry (e.g., 10 minutes)
        if user.otp_created_at and timezone.now() > user.otp_created_at + timedelta(minutes=10):
            raise serializers.ValidationError(
                {"otp": "OTP has expired. Please request a new one."})

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.is_verified = True
        user.otp = None  # Clear the OTP
        user.save()
        return user


# Use ModelSerializer
class LimitedAppFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppFeature
        fields = ['id', 'name', 'tag']


class MyUserDetailsSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=MyUser.objects.all())

    class Meta:
        model = MyUserDetails
        fields = [
            'id', 'user', 'address', 'phone_number', 'date_of_birth',
            'profile_picture', 'user_signature', 'blood_group', 'gender'
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    features = serializers.PrimaryKeyRelatedField(
        many=True, queryset=AppFeature.objects.all())

    class Meta:
        model = Subscription
        fields = [
            'id', 'package_name', 'package_price', 'features'
        ]


class SubscriptionHistorySerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), required=False, allow_null=True)
    subscription = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.all(), required=False, allow_null=True)
    features = serializers.PrimaryKeyRelatedField(
        queryset=AppFeature.objects.all(), many=True, required=False)
    feature_details = AppFeatureSerializer(
        many=True, source='features', read_only=True
    )
    branch_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SubscriptionHistory
        fields = [
            'id', 'company', 'uid', 'subscription', 'features', 'package_duration', 'paid', 'payment', 'is_active', 'activate_by', 'feature_details', "registration_step", "branch_name"
        ]
        read_only = ['paid', 'payment', 'is_active', 'activate_by', 'uid']

    def get_branch_name(self, obj):
        return obj.branch.name if obj.branch else None

    @transaction.atomic
    def create(self, validated_data):
        request = self.context['request']
        user = request.user

        subscription = validated_data.pop('subscription', None)
        feature_list = validated_data.pop('features', None)
        duration = validated_data.get('package_duration')

        payment = 0
        subscription_name = None

        if feature_list:
            payment = sum([f.price or 0 for f in feature_list])
        elif subscription:
            payment = subscription.package_price or 0
            subscription_name = subscription.package_name

        instance = SubscriptionHistory.objects.create(
            user=user,
            subscription=subscription,
            payment=payment,
            **validated_data
        )
        send_custom_email(
            user=user,
            data={
                "duration": duration,
                "payment": payment,
                "subscription_name": subscription_name if subscription_name else "Customized Subscription"
            },
            email_type="subscription_info"
        )

        if subscription:
            instance.features.set(subscription.features.all())
        elif feature_list:
            instance.features.set(feature_list)

        instance.uid = generate_unique_token(instance.id)
        instance.save()
        return instance


class SubscriptionHistoryPartialUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionHistory
        fields = ['paid', 'activate_by']


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not MyUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "No user is associated with this email.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        try:
            validate_password(data['password'])
        except DjangoValidationError as e:
            raise DRFValidationError({'password': list(e.messages)})
        return data

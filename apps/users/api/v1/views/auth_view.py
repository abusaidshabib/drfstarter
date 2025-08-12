"""
User application view
"""

import logging
import random
from collections import defaultdict
from typing import Any, Dict

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, transaction
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, serializers, status, views
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken,
                                                             OutstandingToken)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.utils import (format_response, generate_random_token,
                             send_custom_email, user_branches_company)
from apps.users.api.v1.serializers import (
    AppFeatureSerializer, CompanySerializer, ForgotPasswordSerializer,
    MyUserSerializer, OTPVerificationSerializer,
    PasswordResetConfirmSerializer, RegisterUserSerializer,
    ResetPasswordSerializer, SubscriptionHistoryPartialUpdateSerializer,
    SubscriptionHistorySerializer, SubscriptionSerializer,
    UserBranchLayoutSerializer)
from apps.users.models import (AppFeature, Branch, Company, CompanyOTP, MyUser,
                               Subscription, SubscriptionHistory,
                               UserBranchFeatures, UserBranchLayout)

# Create your views here.

logger = logging.getLogger(__name__)


class UserListCreateView(generics.ListCreateAPIView):
    """
    List and create users
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MyUserSerializer
    parser_classes = [FormParser, MultiPartParser]

    def get_queryset(self) -> QuerySet[MyUser]:
        _, _, branches = user_branches_company(self.request)
        branch_id = self.request.GET.get('branch', None)
        branch = Branch.objects.none()
        if branch_id:
            try:
                branch = Branch.objects.get(id=int(branch_id))
            except (ValueError, Branch.DoesNotExist):
                raise ValidationError({"branch": "Invalid branch ID."})
            if branch not in branches:
                raise ValidationError(
                    {"branch": "You do not have access to this branch."})
            else:
                MyUser.objects.filter(
                    assigned_branches=branch).exclude(email=self.request.user.email).distinct()
        if not branches:
            return MyUser.objects.none()  # Return empty queryset if no branches
        return MyUser.objects.filter(assigned_branches__in=branches).exclude(email=self.request.user.email).distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return format_response({
            'message': 'User list retrieved successfully',
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return format_response({
            'message': 'User created successfully',
            'results': serializer.data
        }, status_code=status.HTTP_201_CREATED)


class UserRegistrationView(generics.CreateAPIView):

    """
    Only for Company owner registration
    """
    pagination_class = [AllowAny]
    serializer_class = RegisterUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Create response
        response = format_response({
            'message': 'User registered successfully',
            'results': serializer.data
        }, status_code=status.HTTP_201_CREATED)

        # Set cookies
        response.set_cookie(
            key='access_token',
            value=access_token,
            max_age=settings.SESSION_COOKIE_ACCESS_TOKEN_MAX_AGE,
            secure=settings.SESSION_COOKIE_SECURE,
            httponly=settings.SESSION_COOKIE_HTTPONLY,
            samesite=settings.SESSION_COOKIE_SAMESITE
        )
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            max_age=settings.SESSION_COOKIE_REFRESH_TOKEN_MAX_AGE,
            secure=settings.SESSION_COOKIE_SECURE,
            httponly=settings.SESSION_COOKIE_HTTPONLY,
            samesite=settings.SESSION_COOKIE_SAMESITE
        )

        return response


class VerifyOTPView(views.APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email', None)
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = MyUser.objects.get(email=email)
        except MyUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = OTPVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user.is_verified = True
        user.otp = None
        user.save()

        # If user has two-step enabled, generate tokens and set cookies here
        if user.is_two_step:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = Response({
                "message": "OTP verified successfully. User is now fully authenticated."
            }, status=status.HTTP_200_OK)

            response.set_cookie(
                key='access_token',
                value=access_token,
                max_age=settings.SESSION_COOKIE_ACCESS_TOKEN_MAX_AGE,
                secure=settings.SESSION_COOKIE_SECURE,
                httponly=settings.SESSION_COOKIE_HTTPONLY,
                samesite=settings.SESSION_COOKIE_SAMESITE
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                max_age=settings.SESSION_COOKIE_REFRESH_TOKEN_MAX_AGE,
                secure=settings.SESSION_COOKIE_SECURE,
                httponly=settings.SESSION_COOKIE_HTTPONLY,
                samesite=settings.SESSION_COOKIE_SAMESITE
            )

            return response

        return Response({
            "message": "OTP verified successfully. User is now verified."
        }, status=status.HTTP_200_OK)


class ResendOTPView(views.APIView):

    def post(self, request):
        email = request.data.get('email')
        try:
            user = MyUser.objects.get(email=email)
        except MyUser.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

        # if user.is_verified:
        #     return Response({"message": "User already verified."}, status=400)

        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()
        send_custom_email(user, {"otp": otp}, "signup_otp")

        return Response({"message": "OTP resent successfully."}, status=200)


class UserGetUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MyUserSerializer
    parser_classes = [FormParser, MultiPartParser]
    lookup_field = 'pk'

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        if user.is_superuser or getattr(user, 'is_owner', False):
            return MyUser.objects.all()

        _, _, branches = user_branches_company(self.request)
        return MyUser.objects.filter(assigned_branches__in=branches).distinct()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return format_response({
            'message': 'User retrieved successfully',
            'results': serializer.data
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return format_response({
            'message': 'User updated successfully',
            'results': serializer.data
        }, status_code=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return format_response({
            'message': 'User deleted successfully',
            'results': {}
        }, status_code=status.HTTP_204_NO_CONTENT)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom Token Obtain Pair View
    """

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            access_token = response.data.get("access", None)
            refresh_token = response.data.get("refresh", None)
            email = request.data.get('email')
            user = MyUser.objects.get(email=email)

            response.data = {
                "message": "Logged in successfully"
            }
            if not user.is_two_step:
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    max_age=settings.SESSION_COOKIE_ACCESS_TOKEN_MAX_AGE,
                    secure=settings.SESSION_COOKIE_SECURE,
                    httponly=settings.SESSION_COOKIE_HTTPONLY,
                    samesite=settings.SESSION_COOKIE_SAMESITE
                )
                response.set_cookie(
                    key='refresh_token',
                    value=refresh_token,
                    max_age=settings.SESSION_COOKIE_REFRESH_TOKEN_MAX_AGE,
                    secure=settings.SESSION_COOKIE_SECURE,
                    httponly=settings.SESSION_COOKIE_HTTPONLY,
                    samesite=settings.SESSION_COOKIE_SAMESITE
                )
                return response
            else:
                otp = str(random.randint(100000, 999999))
                user.otp = otp
                user.otp_created_at = timezone.now()
                user.save()
                send_custom_email(user, {'otp': otp}, email_type="signup_otp")
                return format_response(
                    {
                        "message": "PLease use token to move farther",
                        "results": {},
                    }, status_code=status.HTTP_200_OK
                )
        except Exception as e:
            logger.error("Refresh token error: %s", {str(e)})
            raise


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(generics.GenericAPIView):
    """
    View to handle user logouts.
    """
    permission_classes = [AllowAny]  # Allows logout even if token expired

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to logout user and delete refresh
        """
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except (TokenError, InvalidToken) as e:
                    logger.warning(
                        "Refresh token issue in get_queryset: %s", str(e))
                    # Optional: Log the error but don't interrupt logout

            response = format_response(
                {"message": "Logged out successfully."},
                status_code=status.HTTP_200_OK
            )

            response.delete_cookie(
                key='access_token',
                samesite=settings.SESSION_COOKIE_SAMESITE
            )
            response.delete_cookie(
                key='refresh_token',
                samesite=settings.SESSION_COOKIE_SAMESITE
            )

            return response

        except (InvalidToken, TokenError) as e:
            logger.error("Logout error: %s", {str(e)})
            return format_response(
                {"error": _("Logout failed. Please try again later.")},
                status_code=status.HTTP_400_BAD_REQUEST
            )


class TokenValidateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = MyUserSerializer(user, context={"request": request})
        return format_response(
            {
                "message": "Token is valid",
                "results": serializer.data
            }, status_code=status.HTTP_200_OK
        )


class GetCookieView(generics.GenericAPIView):
    """
    Get access token from cookies.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        access_value = request.COOKIES.get('access_token', 'No cookie found')
        refresh_value = request.COOKIES.get('refresh_token', 'No cookie found')

        return format_response({
            'message': 'Cookie retrieve successfully',
            'results': {
                'access_value': access_value,
                'refresh_value': refresh_value
            }
        }, status_code=status.HTTP_202_ACCEPTED)


class CompanyListCreateView(generics.CreateAPIView):
    """
    List and create a new company instance.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CompanySerializer
    parser_classes = [FormParser, MultiPartParser]

    def get_queryset(self):

        user, company, branches = user_branches_company(self.request)
        return company

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return format_response({
            'message': 'Company created successfully',
            'results': serializer.data
        }, status_code=status.HTTP_201_CREATED)


class CompanyGetUpdateView(generics.RetrieveUpdateDestroyAPIView):
    """
    CompanyGetUpdateView is a class based view that
    """
    permission_classes = [AllowAny]
    serializer_class = CompanySerializer
    parser_classes = [FormParser, MultiPartParser]

    def get_object(self):
        company_name = self.request.query_params.get('name') or None
        if company_name:
            return get_object_or_404(Company, name=company_name)
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'company'):
            return user.company
        raise Company.DoesNotExist("Company not found.")

    def get(self, request, *args, **kwargs):
        try:
            company = self.get_object()
            serializer = self.get_serializer(company)
            return format_response({
                'message': 'Company get successfully',
                'results': serializer.data
            }, status_code=status.HTTP_201_CREATED)

        except Company.DoesNotExist:
            return Response({"error": "Company not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        """
        Handles both PUT (full update) and PATCH (partial update).
        """
        partial = kwargs.pop('partial', False) or (
            request.method.lower() == 'patch')
        try:
            company = self.get_object()
            serializer = self.get_serializer(
                company, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return format_response({
                'message': 'Company updated successfully',
                'results': serializer.data
            }, status_code=status.HTTP_200_OK)

        except Company.DoesNotExist:
            return Response({"error": "Company not found."}, status=status.HTTP_404_NOT_FOUND)
        except serializers.ValidationError as e:
            return Response({"errors": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeaturesListView(generics.ListAPIView):
    """
    List all features that are available for the user
    """
    permission_classes = [AllowAny]
    serializer_class = AppFeatureSerializer

    def get_queryset(self):
        try:
            return AppFeature.objects.filter(feature_type='paid').order_by('order')
        except (ObjectDoesNotExist, DatabaseError, AttributeError) as e:
            logging.exception(
                "Error in FeaturesListView.get_queryset: %s", str(e))
            return AppFeature.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return format_response({
            'message': 'Features list retrieved successfully',
            'results': serializer.data
        })


class SubscriptionListCreateView(generics.ListCreateAPIView):
    """
    SubscriptionListCreateView is a class based view
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        print(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return format_response({
            'message': 'Subscription list retrieved successfully',
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return format_response({
            'message': 'Subscription created successfully',
            'results': serializer.data
        }, status_code=status.HTTP_201_CREATED)


class SubscriptionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    SubscriptionRetrieveUpdateDestroyView is a
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return format_response({
            'message': 'Subscriptions retrieved successfully',
            'results': serializer.data
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return format_response({
            'message': 'Subscriptions updated successfully',
            'results': serializer.data
        }, status_code=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return format_response({
            'message': 'Subscriptions deleted successfully',
            'results': {}
        }, status_code=status.HTTP_204_NO_CONTENT)


# --- SubscriptionHistory Views ---

class SubscriptionHistoryListCreateView(generics.ListCreateAPIView):
    queryset = SubscriptionHistory.objects.all()
    serializer_class = SubscriptionHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user, _, _ = user_branches_company(self.request)
        return SubscriptionHistory.objects.filter(user=user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return format_response({
            'message': 'Subscription history retrieved successfully',
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return format_response({
            'message': 'Subscription history created successfully',
            'results': serializer.data
        }, status_code=status.HTTP_201_CREATED)


token_generator = PasswordResetTokenGenerator()


class SubscriptionHistoryDetailUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SubscriptionHistory.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return SubscriptionHistoryPartialUpdateSerializer
        return SubscriptionHistorySerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return format_response({
            'message': 'Subscription history retrieved successfully',
            'results': serializer.data
        })

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        instance = self.get_object()

        with transaction.atomic():

            # Inject default data if request.data is empty
            token = generate_random_token()

            # Company.objects.create(token=token)

            data = {
                'paid': True,
                'activate_by': request.user.pk
            }

            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            send_custom_email(instance.user, {'token': token},
                              email_type='subscription_token')

        return format_response({
            'message': 'Subscription history updated successfully',
            'results': {}
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return format_response({
            'message': 'Subscription history deleted successfully',
            'results': None
        })


token_generator = PasswordResetTokenGenerator()


class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        # ✅ Check if old password is correct
        if not user.check_password(old_password):
            return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Set new password and save
        user.set_password(new_password)
        user.save()

        # ✅ Create response first
        response = format_response({
            'message': 'Password changed successfully. You have been logged out from all devices.',
            'results': None
        }, status_code=status.HTTP_200_OK)

        # ✅ Delete refresh_token cookie
        response.delete_cookie(
            key='refresh_token',
            samesite=settings.SESSION_COOKIE_SAMESITE,
        )
        response.delete_cookie(
            key='access_token',
            samesite=settings.SESSION_COOKIE_SAMESITE,
        )

        # ✅ Blacklist all outstanding tokens
        try:
            tokens = OutstandingToken.objects.filter(user=user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception as e:
            logger.error(f"Error blacklisting tokens: {str(e)}")

        return response


class ForgotPasswordView(views.APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        try:
            user = MyUser.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_BASE_URL}/reset-password/{uidb64}/{token}/"
            send_custom_email(
                user, data={"reset_url": reset_url}, email_type="reset_password")
        except MyUser.DoesNotExist:
            # Prevent user enumeration
            pass

        return Response(
            {"message": "If the email is valid, a reset link has been sent."},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(views.APIView):
    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data: Dict[str, Any] = serializer.validated_data

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = MyUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, MyUser.DoesNotExist):
            return Response({"error": "Invalid link"}, status=status.HTTP_400_BAD_REQUEST)

        if not token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(validated_data['password'])
        user.save()

        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)


class ValidPaymentToken(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        token = request.data.get('token')
        subscription_history_id = request.data.get('subscription_id')

        try:
            otp = CompanyOTP.objects.get(token=token, used=False)
            subscription = SubscriptionHistory.objects.get(id=subscription_history_id)
            create_permission = ""
            otp.used = True
            otp.save()
            user.token_valid = True
            if not request.user.company:
                create_permission = 'Company'
                user.company_create = True
            else:
                create_permission = 'Branch'
                user.branch_create = True
            user.save()
            subscription.registration_step = 'token_verified'
            subscription.save()
        except CompanyOTP.DoesNotExist:
            return format_response({
                'message': 'Invalid or already used token',
                'errors': {'token': 'Invalid or expired token'}
            }, status_code=status.HTTP_400_BAD_REQUEST)
        except SubscriptionHistory.DoesNotExist:
            return format_response({
                'message': 'Subscription history not found',
                'errors': {'subscription_id': 'Invalid subscription ID'}
            }, status_code=status.HTTP_404_NOT_FOUND)

        return format_response({
            'message': f'{create_permission} token is valid',
            'results': {}
        }, status_code=status.HTTP_200_OK)


class UserBranchLayoutAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, branch_id):
        try:
            return UserBranchLayout.objects.get(user=request.user, branch_id=branch_id)
        except UserBranchLayout.DoesNotExist:
            raise NotFound("Layout not found for this branch.")

    def get(self, request, branch_id):
        layout = self.get_object(request, branch_id)
        serializer = UserBranchLayoutSerializer(layout)
        data = serializer.data
        return format_response({
            "message": "Layout retrieved successfully",
            "results": data['position']
        }, status_code=status.HTTP_200_OK)

    def post(self, request, branch_id):
        # Prevent duplicate layout
        if UserBranchLayout.objects.filter(user=request.user, branch_id=branch_id).exists():
            return format_response(
                {"message": "Layout already exists for this branch."},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer = UserBranchLayoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, branch_id=branch_id)
        return format_response({
            "message": "Layout created successfully",
            "results": serializer.data['position']
        }, status_code=status.HTTP_201_CREATED)

    def patch(self, request, branch_id):
        layout = self.get_object(request, branch_id)
        serializer = UserBranchLayoutSerializer(
            layout, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return format_response({
            "message": "Layout updated successfully",
            "results": serializer.data['position']
        })

    def delete(self, request, branch_id):
        layout = self.get_object(request, branch_id)
        layout.delete()
        return format_response(
            {"message": "Layout deleted successfully"},
            status_code=status.HTTP_204_NO_CONTENT
        )


class RetrievePermissionListAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _, _, branches = user_branches_company(request)

        branches_id = request.GET.get('branches_id')
        if branches_id:
            try:
                branch_id_list = [int(bid.strip()) for bid in branches_id.split(
                    ',') if bid.strip().isdigit()]
                branches = branches.filter(id__in=branch_id_list)
            except ValueError:
                return Response({
                    "status": "error",
                    "message": "Invalid branch ID format.",
                    "results": []
                }, status=status.HTTP_400_BAD_REQUEST)

        result = []

        for branch in branches:
            if getattr(request.user, "is_owner", False):
                user_feature_ids = set(
                    AppFeature.objects.values_list('id', flat=True)
                )
            else:
                try:
                    user_branch_features = request.user.user_branch_features.get(
                        branch=branch)
                    user_feature_ids = set(
                        user_branch_features.features.values_list('id', flat=True)
                    )
                except UserBranchFeatures.DoesNotExist:
                    user_feature_ids = set()

            if not user_feature_ids:
                result.append({
                    "branch_id": branch.id,
                    "branch_name": branch.name,
                    "branch_features": []
                })
                continue

            common_features = AppFeature.objects.filter(
                id__in=user_feature_ids
            ).order_by('order')

            grouped = defaultdict(list)
            for feature in common_features:
                tag = feature.tag.lower()
                if 'companysettings' in tag:
                    grouped['company'].append({
                        "id": feature.id,
                        "name": feature.name
                    })
                elif '_' in tag:
                    base_name, operation = tag.split('_', 1)
                    grouped[base_name.lower()].append({
                        "id": feature.id,
                        "name": operation.lower()
                    })
                else:
                    grouped['features'].append({
                        "id": feature.id,
                        "name": feature.name,
                        "tag": feature.tag
                    })
            branch_result = [
                {
                    "name": group,
                    "operations": features
                } for group, features in grouped.items()
            ]

            result.append({
                "branch_id": branch.id,
                "branch_name": branch.name,
                "branch_features": branch_result
            })

        return Response({
            "status": "success",
            "message": "Permission list retrieved successfully.",
            "results": result
        }, status=status.HTTP_200_OK)


class UserRetrievePermissionListAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id=None):
        _, _, branches = user_branches_company(request)
        branches_id_param = request.GET.get('branches_id')
        if not branches_id_param:
            return Response({
                "status": "error",
                "message": "branches_id parameter is required.",
                "results": []
            }, status=status.HTTP_400_BAD_REQUEST)

        branch_id_list = [bid.strip() for bid in branches_id_param.split(
            ',') if bid.strip().isdigit()]
        if not branch_id_list:
            return Response({
                "status": "error",
                "message": "No valid branch IDs found.",
                "results": []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate target user
        try:
            target_user = MyUser.objects.get(id=user_id)
        except MyUser.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Target user not found.",
                "results": []
            }, status=status.HTTP_404_NOT_FOUND)

        request_user_branch_features_qs = UserBranchFeatures.objects.filter(
            user=request.user)
        request_user_branch_map = {
            ubf.branch_id: set(ubf.features.values_list('id', flat=True))
            for ubf in request_user_branch_features_qs
        }

        all_branch_results = []

        for branch_id in branch_id_list:
            try:
                branch = Branch.objects.get(id=int(branch_id))
            except Branch.DoesNotExist:
                all_branch_results.append({
                    "branch_id": branch_id,
                    "branch_name": None,
                    "operations": [],
                    "error": "Branch not found."
                })
                continue

            # Target user features for this branch
            try:
                target_branch_features = target_user.user_branch_features.get(
                    branch=branch)
                target_feature_ids = set(
                    target_branch_features.features.values_list('id', flat=True))
            except UserBranchFeatures.DoesNotExist:
                target_feature_ids = set()

            # Request user features for this branch
            request_feature_ids = request_user_branch_map.get(branch.id, set())

            # Branch-level feature restriction
            branch_feature_ids = set(
                branch.features.values_list('id', flat=True))

            merged_feature_ids = (request_feature_ids |
                                  target_feature_ids) & branch_feature_ids

            all_features = AppFeature.objects.filter(
                id__in=merged_feature_ids).order_by('order')

            grouped = defaultdict(list)
            for feature in all_features:
                tag = feature.tag.lower()
                feature_id = feature.id

                allowed = feature_id in target_feature_ids
                disabled = allowed and (feature_id not in request_feature_ids)

                if 'companysettings' in tag:
                    group_key = 'company'
                    name = feature.name
                elif '_' in tag:
                    base_name, operation = tag.split('_', 1)
                    group_key = base_name
                    name = operation
                else:
                    group_key = 'features'
                    name = feature.name

                grouped[group_key].append({
                    "id": feature.id,
                    "name": name.lower(),
                    "allowed": allowed,
                    "disabled": disabled
                })

            branch_result = [
                {
                    "name": group,
                    "operations": operations
                } for group, operations in grouped.items()
            ]

            all_branch_results.append({
                "branch_id": branch.id,
                "branch_name": branch.name,
                "branch_features": branch_result
            })

        return Response({
            "status": "success",
            "message": "Multi-branch permission list retrieved.",
            "results": all_branch_results
        }, status=status.HTTP_200_OK)

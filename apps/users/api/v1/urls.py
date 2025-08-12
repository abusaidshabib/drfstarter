from django.urls import path

from apps.users.api.v1.views import (BranchGetUpdateDeleteView,
                                     BranchListCreateView,
                                     CompanyGetUpdateView,
                                     CompanyListCreateView,
                                     CustomTokenObtainPairView,
                                     FeaturesListView, ForgotPasswordView,
                                     GetCookieView, LogoutView,
                                     PasswordResetConfirmView, ResendOTPView,
                                     ResetPasswordView,
                                     RetrievePermissionListAPIView,
                                     SubscriptionHistoryDetailUpdateDeleteView,
                                     SubscriptionHistoryListCreateView,
                                     SubscriptionListCreateView,
                                     SubscriptionRetrieveUpdateDestroyView,
                                     TokenValidateView,
                                     UserBranchLayoutAPIView,
                                     UserGetUpdateView, UserListCreateView,
                                     UserRegistrationView,
                                     UserRetrievePermissionListAPIView,
                                     ValidPaymentToken, VerifyOTPView)

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='Login'),
    path('registration/', UserRegistrationView.as_view(), name='user-registration'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/validate/', TokenValidateView.as_view(),
         name='token_validate_with_user_details'),
    path('payment/validate/', ValidPaymentToken.as_view(), name='validate-payment'),

    path('forget-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('forget-password/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(), name='forget-password-changed'),

    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),

    path('otp-verify/', VerifyOTPView.as_view(), name='otp-verify'),
    path('otp-resend/', ResendOTPView.as_view(), name='resend-otp'),

    path('get-cookie/', GetCookieView.as_view(), name='get_cookie'),
    path('company/', CompanyGetUpdateView.as_view(), name="company"),
    path('companies/', CompanyListCreateView.as_view(), name='company-details'),
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserGetUpdateView.as_view(), name='user-list-create'),
    path('branch/', BranchListCreateView.as_view(), name="branch_create_list"),
    path('branch/<int:pk>/', BranchGetUpdateDeleteView.as_view(),
         name="branch_create_list"),
    path('features/', FeaturesListView.as_view(), name="features_list"),
    path('subscription/', SubscriptionListCreateView.as_view(),
         name='subscription-list'),
    path('subscription/<int:pk>/',
         SubscriptionRetrieveUpdateDestroyView.as_view(), name='subscription-detail'),
    path('subscription-history/', SubscriptionHistoryListCreateView.as_view(),
         name="subscription_history"),
    path('subscription-history/<int:pk>/',
         SubscriptionHistoryDetailUpdateDeleteView.as_view(), name='subscription-accept'),

    path('<int:branch_id>/user-branch-layout/',
         UserBranchLayoutAPIView.as_view(), name='userbranchlayout-crud'),

    path('permission-list/',
         RetrievePermissionListAPIView.as_view(), name='retrieve-permission-list'),

    path('user/permission-list/<int:user_id>/',
         UserRetrievePermissionListAPIView.as_view(), name='user-retrieve-permission-list'),
]

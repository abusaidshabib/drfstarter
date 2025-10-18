from django.conf import settings
from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class JWTCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        skip_paths = ["/api/v1/token/", "/api/v1/logout/"]
        if request.path in skip_paths:
            return self.get_response(request)

        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token', None)

        new_access_token = None
        tokens_invalid = False

        if access_token:
            try:
                AccessToken(access_token)
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
                request.jwt_token = access_token
            except TokenError:
                if refresh_token:
                    try:
                        refresh = RefreshToken(refresh_token)
                        new_access_token = str(refresh.access_token)
                        request.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access_token}'
                        request.jwt_token = new_access_token
                    except TokenError:
                        tokens_invalid = True
                else:
                    tokens_invalid = True
        elif refresh_token:
            try:
                refresh = RefreshToken(refresh_token)
                new_access_token = str(refresh.access_token)
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access_token}'
                request.jwt_token = new_access_token
            except TokenError:
                tokens_invalid = True

        if tokens_invalid:
            response = JsonResponse(
                {'message': 'Session expired. Please log in again.', 'errors': "logout"},
                status=401
            )
            response.delete_cookie(
                'access_token', samesite=settings.SESSION_COOKIE_SAMESITE)
            response.delete_cookie(
                'refresh_token', samesite=settings.SESSION_COOKIE_SAMESITE)
            return response

        response = self.get_response(request)

        if new_access_token:
            response.set_cookie(
                key='access_token',
                value=new_access_token,
                max_age=settings.SESSION_COOKIE_ACCESS_TOKEN_MAX_AGE,  # 1 hour
                secure=settings.SESSION_COOKIE_SECURE,
                httponly=settings.SESSION_COOKIE_HTTPONLY,
                samesite=settings.SESSION_COOKIE_SAMESITE
            )

        return response

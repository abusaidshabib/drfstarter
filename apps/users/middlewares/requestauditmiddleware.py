import logging

from django.urls import resolve
from django.http import HttpRequest, HttpResponse
from django.core.exceptions import ValidationError

from apps.users.models import RequestAuditLog, MyUser

logger = logging.getLogger(__name__)


class RequestAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = request.user if request.user.is_authenticated else None
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        ip_address = None
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        path = request.path
        method = request.method

        response = self.get_response(request)

        status_code = response.status_code

        try:
            RequestAuditLog.objects.create(
                user=user if isinstance(user, MyUser) else None,
                ip_address=ip_address,
                user_agent=user_agent,
                path=path,
                method=method,
                status_code=status_code
            )
        except ValidationError as e:
            logger.error(f"Failed to save audit log: {e}")

        return response

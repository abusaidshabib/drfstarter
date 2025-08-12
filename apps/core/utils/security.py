from django.conf import settings
from django.core.exceptions import PermissionDenied


def match_add_new_order_secret_key(provided_key):

    if settings.ADD_NEW_ORDER_KEY != provided_key:
        raise PermissionDenied("Invalid secret key.")
    return True


def match_secret_key(request):
    provided_key = request.headers.get('X-Secret-Key', None)
    if not provided_key:
        raise PermissionDenied("Secret key is missing.")

    # Ensure AI_SECURITY_KEYS is available
    valid_keys = getattr(settings, 'AI_SECURITY_KEYS', [])
    if provided_key in valid_keys:
        return True
    raise PermissionDenied("Invalid secret key.")

import secrets
import string


def generate_random_token(length=64):
    chars = string.ascii_letters + string.digits  # a-zA-Z0-9
    return ''.join(secrets.choice(chars) for _ in range(length))

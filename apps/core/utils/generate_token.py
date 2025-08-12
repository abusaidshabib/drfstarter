import hashlib


def generate_unique_token(unique_number: int) -> str:
    # Create SHA-256 hash from the number
    hash_hex = hashlib.sha256(str(unique_number).encode("utf-8")).hexdigest()

    # Convert hash to an integer
    hash_int = int(hash_hex, 16)

    # Convert to base36 (0-9, a-z)
    base36_chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    base36 = ""
    while hash_int > 0:
        hash_int, i = divmod(hash_int, 36)
        base36 = base36_chars[i] + base36
    return base36[:6]

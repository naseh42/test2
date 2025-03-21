import uuid

def validate_uuid(u: str) -> bool:
    """
    بررسی فرمت UUID.
    Args:
        u (str): رشته UUID.
    Returns:
        bool: معتبر بودن یا نبودن UUID.
    """
    try:
        uuid.UUID(u)
        return True
    except ValueError:
        return False

def generate_random_string(length: int = 12) -> str:
    """
    تولید رشته تصادفی.
    Args:
        length (int): طول رشته، پیش‌فرض: 12.
    Returns:
        str: رشته تصادفی.
    """
    return uuid.uuid4().hex[:length]

import hashlib

def generate_hash(data: str) -> str:
    """
    تولید هش با استفاده از SHA256.
    Args:
        data (str): داده ورودی.
    Returns:
        str: هش تولید شده.
    """
    return hashlib.sha256(data.encode()).hexdigest()

def check_password_strength(password: str) -> bool:
    """
    بررسی قدرت رمز عبور.
    Args:
        password (str): رمز عبور.
    Returns:
        bool: قوی بودن یا نبودن رمز عبور.
    """
    return len(password) >= 8 and any(char.isdigit() for char in password) and any(char.isalpha() for char in password)

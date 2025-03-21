from urllib.parse import urlparse
import requests

def validate_url(url: str) -> bool:
    """
    بررسی معتبر بودن یک URL.
    Args:
        url (str): آدرس URL.
    Returns:
        bool: معتبر بودن یا نبودن.
    """
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

def extract_domain(url: str) -> str:
    """
    استخراج دامنه از URL.
    Args:
        url (str): آدرس URL.
    Returns:
        str: دامنه استخراج شده.
    """
    parsed = urlparse(url)
    return parsed.netloc

def fetch_data_from_api(url: str, params: dict = None) -> dict:
    """
    ارسال درخواست GET به API و دریافت داده.
    Args:
        url (str): آدرس API.
        params (dict): پارامترهای کوئری.
    Returns:
        dict: داده‌های دریافتی از API.
    """
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

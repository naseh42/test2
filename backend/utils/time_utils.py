from datetime import datetime, timedelta
import pytz

def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    تبدیل تاریخ به فرمت مشخص شده.
    Args:
        dt (datetime): تاریخ و زمان مورد نظر.
        format (str): فرمت دلخواه، پیش‌فرض: YYYY-MM-DD HH:MM:SS.
    Returns:
        str: تاریخ فرمت‌شده.
    """
    return dt.strftime(format)

def calculate_time_difference(start: datetime, end: datetime) -> timedelta:
    """
    محاسبه اختلاف زمانی بین دو تاریخ.
    Args:
        start (datetime): تاریخ شروع.
        end (datetime): تاریخ پایان.
    Returns:
        timedelta: اختلاف زمانی.
    """
    return end - start

def get_current_time(timezone: str = "UTC") -> datetime:
    """
    دریافت زمان فعلی در منطقه زمانی مشخص شده.
    Args:
        timezone (str): منطقه زمانی، پیش‌فرض: UTC.
    Returns:
        datetime: زمان فعلی.
    """
    tz = pytz.timezone(timezone)
    return datetime.now(tz)

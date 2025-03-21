import logging

def setup_logger(name: str = "app_logger", level: int = logging.INFO) -> logging.Logger:
    """
    تنظیم لاگر برای ثبت اطلاعات.
    Args:
        name (str): نام لاگر، پیش‌فرض: app_logger.
        level (int): سطح لاگ، پیش‌فرض: INFO.
    Returns:
        logging.Logger: شیء لاگر تنظیم‌شده.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # قالب لاگ
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # هندلر کنسول
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

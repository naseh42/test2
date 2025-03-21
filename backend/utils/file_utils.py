import os

def read_file(file_path: str) -> str:
    """
    خواندن محتویات یک فایل.
    Args:
        file_path (str): مسیر فایل.
    Returns:
        str: محتوای فایل.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def write_file(file_path: str, content: str) -> None:
    """
    نوشتن محتوا در یک فایل.
    Args:
        file_path (str): مسیر فایل.
        content (str): محتوایی که باید نوشته شود.
    """
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

def ensure_directory_exists(directory_path: str) -> None:
    """
    اطمینان از وجود مسیر. اگر مسیر وجود نداشته باشد، آن را ایجاد می‌کند.
    Args:
        directory_path (str): مسیر پوشه.
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def delete_file(file_path: str) -> None:
    """
    حذف فایل.
    Args:
        file_path (str): مسیر فایل.
    """
    if os.path.exists(file_path):
        os.remove(file_path)

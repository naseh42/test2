import qrcode
from io import BytesIO

def generate_qr_code(data: str, file_path: str = None) -> BytesIO:
    """
    تولید QR Code برای داده ورودی.
    Args:
        data (str): داده‌ای که به QR Code تبدیل می‌شود.
        file_path (str): (اختیاری) مسیر ذخیره QR Code به‌عنوان فایل.
    Returns:
        BytesIO: شیء QR Code به صورت بایت‌ها.
    """
    qr = qrcode.QRCode(
        version=1,  # تنظیم پیچیدگی QR Code (1 ساده‌ترین)
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,  # اندازه هر خانه در QR Code
        border=4,  # میزان فاصله حاشیه
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white")
    
    if file_path:
        img.save(file_path)  # ذخیره به‌عنوان فایل
        return None
    else:
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

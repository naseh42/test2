from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
from backend.utils.network_utils import validate_url, extract_domain
from backend.utils.qr_utils import generate_qr_code

# تنظیم مسیر تمپلت‌ها
templates = Jinja2Templates(directory="backend/templates")

# ایجاد Router
router = APIRouter()

# مسیر بخش دامنه‌ها
@router.get("/", tags=["Domains"])
def domains_page(request: Request):
    return templates.TemplateResponse("domains.html", {"request": request})

# مسیر بررسی URL و استخراج دامنه
@router.get("/validate-url", tags=["Network Tools"])
def validate_url_api(url: str = Query(..., description="URL to validate")):
    is_valid = validate_url(url)
    domain = extract_domain(url) if is_valid else None
    return {
        "url": url,
        "is_valid": is_valid,
        "domain": domain
    }

# مسیر تولید QR Code
@router.get("/generate-qr", tags=["QR Code"])
def generate_qr(data: str = Query(..., description="Data to encode in QR Code")):
    qr_buffer = generate_qr_code(data)
    return StreamingResponse(qr_buffer, media_type="image/png")

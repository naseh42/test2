from backend.utils.file_utils import ensure_directory_exists, delete_file
from backend.utils.network_utils import validate_url, extract_domain
import os
import secrets
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

# آی‌پی عمومی سرور (می‌توانید آن را دستی وارد کنید یا از متغیر محیطی استفاده کنید)
SERVER_IP = os.getenv("SERVER_IP", "127.0.0.1")  # مثال: "your-server-ip"

# ایجاد شیء FastAPI
app = FastAPI(
    title="Management Panel API",
    description="Comprehensive API for managing users, domains, settings, and server operations.",
    version="1.0.0"
)

# تنظیم مسیر تمپلت‌ها
templates = Jinja2Templates(directory="backend/templates")

# ایجاد جداول پایگاه داده (در صورت نیاز)
# اطمینان از اینکه `engine` به درستی ایمپورت شده است
from backend.database import engine, Base
Base.metadata.create_all(bind=engine)

# اضافه کردن فایل‌های استاتیک
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# افزودن Middleware برای امنیت و دسترسی‌ها
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # اجازه دسترسی به همه دامنه‌ها برای تست
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # روش‌های مجاز
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", SERVER_IP],  # آی‌پی سرور و لوکال‌ها
)

# تنظیم لاگر
from backend.utils.logger import setup_logger
logger = setup_logger()

# افزودن رویدادهای startup و shutdown
@app.on_event("startup")
async def startup_event():
    from backend.utils.time_utils import get_current_time, format_datetime
    current_time = get_current_time()
    logger.info(f"🚀 Application started at {format_datetime(current_time)}")
    ensure_directory_exists("backend/static")  # اطمینان از وجود مسیر استاتیک

@app.on_event("shutdown")
async def shutdown_event():
    from backend.utils.time_utils import get_current_time, format_datetime
    current_time = get_current_time()
    logger.info(f"🛑 Application shutting down at {format_datetime(current_time)}")

# مدیریت خطاهای عمومی (مثلاً 404 یا 422)
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    logger.warning(f"404 Error: {request.url} not found.")
    return JSONResponse(
        status_code=404,
        content={"message": "The requested resource was not found."},
    )

@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    logger.error(f"422 Validation Error at {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"message": "Validation error occurred.", "details": exc.errors()},
    )

# مسیر تولید QR Code
@app.get("/generate-qr", tags=["QR Code"])
def generate_qr(data: str = Query(..., description="Data to encode in QR Code")):
    from backend.utils.qr_utils import generate_qr_code
    qr_buffer = generate_qr_code(data)
    return StreamingResponse(qr_buffer, media_type="image/png")

# مسیر بررسی URL و استخراج دامنه
@app.get("/validate-url", tags=["Network Tools"])
def validate_url_api(url: str = Query(..., description="URL to validate")):
    is_valid = validate_url(url)
    domain = extract_domain(url) if is_valid else None
    return {
        "url": url,
        "is_valid": is_valid,
        "domain": domain
    }

# مسیر اصلی
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to the Management Panel API. Use /docs for detailed documentation.",
        "status": "Running"
    }

# مسیر داشبورد (تمپلت صفحه اصلی)
@app.get("/dashboard", tags=["Dashboard"])
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_users": 100,
        "online_users": 20,
        "offline_users": 70,
        "inactive_users": 10,
        "cpu_usage": 45,
        "ram_usage": 65,
        "disk_usage": 55,
        "bandwidth_speed": 120
    })

# مسیر بخش کاربران
@app.get("/users", tags=["Users"])
def users_page(request: Request):
    return templates.TemplateResponse("users.html", {"request": request})

# مسیر بخش تنظیمات
@app.get("/settings", tags=["Settings"])
def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

# مسیر بخش دامنه‌ها
@app.get("/domains", tags=["Domains"])
def domains_page(request: Request):
    return templates.TemplateResponse("domains.html", {"request": request})

# مسیر دسترسی ادمین با لینک متغیر
@app.get("/admin-{random_string}", tags=["Admin"])
def admin_access(random_string: str):
    try:
        with open("admin_link.txt", "r") as file:
            saved_link = file.read().strip()
        if f"/admin-{random_string}" not in saved_link:
            raise HTTPException(status_code=403, detail="Invalid admin link.")
        return {"message": "Welcome to the admin panel!"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Admin link not found. Please reinstall the panel.")

# مسیر بازیابی لینک ذخیره‌شده
@app.get("/retrieve-admin-link", tags=["Admin"])
def retrieve_admin_link():
    try:
        with open("admin_link.txt", "r") as file:
            admin_link = file.read().strip()
        return {"admin_link": admin_link}
    except FileNotFoundError:
        return {"message": "Admin link not found. Please reinstall the panel."}

# افزودن روترها
from backend.routers import users, domains, settings
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(domains.router, prefix="/domains", tags=["Domains"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])

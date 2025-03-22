from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from backend.routers import users, domains, settings
from backend.database.database import Base, engine
from backend.utils.logger import setup_logger
from backend.utils.time_utils import format_datetime, get_current_time
from backend.utils.qr_utils import generate_qr_code
from backend.utils.file_utils import ensure_directory_exists, delete_file
from backend.utils.network_utils import validate_url, extract_domain
import os
import subprocess
import secrets

# ایجاد شیء FastAPI
app = FastAPI(
    title="Management Panel API",
    description="Comprehensive API for managing users, domains, settings, and server operations.",
    version="1.0.0"
)

# تنظیم مسیر تمپلت‌ها
templates = Jinja2Templates(directory="backend/templates")

# ایجاد جداول پایگاه داده (در صورت نیاز)
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
    allowed_hosts=["*", "localhost", "127.0.0.1"],  # * برای اجازه‌دادن به تمام دامنه‌ها و آی‌پی‌ها
)

# تنظیم لاگر
logger = setup_logger()

# افزودن رویدادهای startup و shutdown
@app.on_event("startup")
async def startup_event():
    current_time = get_current_time()
    logger.info(f"🚀 Application started at {format_datetime(current_time)}")
    ensure_directory_exists("backend/static")  # اطمینان از وجود مسیر استاتیک

@app.on_event("shutdown")
async def shutdown_event():
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
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(domains.router, prefix="/domains", tags=["Domains"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])

# توابع برای نصب و کانفیگ Uvicorn
def install_uvicorn():
    print("Installing Uvicorn...")
    subprocess.run(["pip", "install", "uvicorn"], check=True)
    print("Uvicorn installed successfully!")

def run_uvicorn_as_service():
    print("Configuring Uvicorn as a service...")
    BASE_DIR = os.path.abspath(os.getcwd())
    service_config = f"""
    [Unit]
    Description=Uvicorn Service
    After=network.target

    [Service]
    User={os.getlogin()}
    WorkingDirectory={BASE_DIR}
    ExecStart={BASE_DIR}/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
    Restart=always

    [Install]
    WantedBy=multi-user.target
    """
    service_path = "/etc/systemd/system/uvicorn.service"
    with open(service_path, "w") as f:
        f.write(service_config)
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "start", "uvicorn"], check=True)
    subprocess.run(["systemctl", "enable", "uvicorn"], check=True)
    print("Uvicorn service configured and started successfully!")

# فراخوانی نصب و کانفیگ در صورت اجرا مستقیم
if __name__ == "__main__":
    print("Starting setup...")
    install_uvicorn()  # نصب Uvicorn
    run_uvicorn_as_service()  # اجرای Uvicorn به‌عنوان سرویس
    print("\nSetup completed successfully! 🚀")

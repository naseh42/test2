import os
import secrets
from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from backend.utils.file_utils import ensure_directory_exists, delete_file
from backend.utils.network_utils import validate_url, extract_domain
from backend.database import engine, Base
from backend.utils.logger import setup_logger

# آی‌پی عمومی سرور
SERVER_IP = os.getenv("SERVER_IP", "127.0.0.1")  # مقدار پیش‌فرض

# ایجاد شیء FastAPI
app = FastAPI(
    title="Management Panel API",
    description="Comprehensive API for managing users, domains, settings, and server operations.",
    version="1.0.0"
)

# تنظیم مسیر تمپلت‌ها
templates = Jinja2Templates(directory="backend/templates")

# ایجاد جداول پایگاه داده
Base.metadata.create_all(bind=engine)

# اضافه کردن فایل‌های استاتیک
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# افزودن Middleware‌ها
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*"]
)

# تنظیم لاگر
logger = setup_logger()

# رویدادهای startup و shutdown
@app.on_event("startup")
async def startup_event():
    from backend.utils.time_utils import get_current_time, format_datetime
    current_time = get_current_time()
    logger.info(f"🚀 Application started at {format_datetime(current_time)}")
    ensure_directory_exists("backend/static")
    favicon_path = "backend/static/favicon.ico"
    if not os.path.exists(favicon_path):
        with open(favicon_path, "w") as f:
            pass

@app.on_event("shutdown")
async def shutdown_event():
    from backend.utils.time_utils import get_current_time, format_datetime
    current_time = get_current_time()
    logger.info(f"🛑 Application shutting down at {format_datetime(current_time)}")

# مدیریت خطاهای عمومی
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

# Middleware لاگ‌برداری
@app.middleware("http")
async def log_request_details(request: Request, call_next):
    logger.debug(f"Headers: {request.headers}")
    logger.debug(f"URL: {request.url}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response

# مسیرهای جدید برای صفحات
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    return templates.TemplateResponse("users.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

# ریدایرکت صفحه اصلی به داشبورد
@app.get("/")
def root():
    return RedirectResponse(url="/dashboard")

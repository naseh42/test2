from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from backend.routers import users, domains, settings
from backend.database import Base, engine
from backend.utils.logger import setup_logger
from backend.utils.time_utils import format_datetime, get_current_time
from backend.utils.qr_utils import generate_qr_code

# ایجاد شیء FastAPI
app = FastAPI(
    title="Management Panel API",
    description="Comprehensive API for managing users, domains, settings, and server operations.",
    version="1.0.0"
)

# ایجاد جداول پایگاه داده (در صورت نیاز)
Base.metadata.create_all(bind=engine)

# اضافه کردن فایل‌های استاتیک
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# افزودن Middleware برای امنیت و دسترسی‌ها
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-production-domain.com"],  # محدود به دامنه‌های معتبر در محیط تولید
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # روش‌های مجاز
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["your-production-domain.com", "*.your-domain.com"],  # محدودیت دامنه‌های مجاز
)

# تنظیم لاگر
logger = setup_logger()

# افزودن رویدادهای startup و shutdown
@app.on_event("startup")
async def startup_event():
    current_time = get_current_time()
    logger.info(f"🚀 Application started at {format_datetime(current_time)}")

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

# افزودن مسیر تولید QR Code
@app.get("/generate-qr", tags=["QR Code"])
def generate_qr(data: str = Query(..., description="Data to encode in QR Code")):
    qr_buffer = generate_qr_code(data)
    return StreamingResponse(qr_buffer, media_type="image/png")

# افزودن روترها
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(domains.router, prefix="/domains", tags=["Domains"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])

# مسیر اصلی
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to the Management Panel API. Use /docs for detailed documentation.",
        "status": "Running"
    }

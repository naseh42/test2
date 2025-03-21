from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from backend.routers import users, domains, settings
from backend.database import Base, engine

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

# افزودن رویدادهای startup و shutdown
@app.on_event("startup")
async def startup_event():
    print("🚀 Application is starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Application is shutting down...")

# مدیریت خطاهای عمومی (مثلاً 404 یا 422)
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": "The requested resource was not found."},
    )

@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content={"message": "Validation error occurred.", "details": exc.errors()},
    )

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

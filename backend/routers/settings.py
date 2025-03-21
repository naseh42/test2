from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.models import Setting, User
from backend.database.database import get_db

router = APIRouter()

# دریافت تنظیمات عمومی سیستم (برای مدیر سیستم)
@router.get("/admin", tags=["Admin"])
def get_all_settings(db: Session = Depends(get_db)):
    settings = db.query(Setting).all()
    if not settings:
        raise HTTPException(status_code=404, detail="No settings found")
    return settings

# دریافت تنظیمات مختص کاربر بر اساس UUID
@router.get("/subscription/{user_uuid}", tags=["Subscription"])
def get_user_settings(user_uuid: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.uuid == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "username": user.username,
        "uuid": user.uuid,
        "traffic_limit": user.traffic_limit,
        "usage_duration": user.usage_duration,
        "simultaneous_connections": user.simultaneous_connections,
    }

# ایجاد لینک اشتراک برای کاربران
@router.get("/generate-link/{user_uuid}", tags=["Subscription"])
def generate_subscription_link(user_uuid: str):
    base_url = "https://your-domain.com/settings/subscription/"
    subscription_link = f"{base_url}{user_uuid}"
    return {"link": subscription_link}

# کپی کردن تنظیمات کاربر
@router.get("/copy-config/{user_uuid}", tags=["Subscription"])
def copy_user_config(user_uuid: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.uuid == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # اطلاعات کانفیگ برای کپی
    return {
        "uuid": user.uuid,
        "traffic_limit": user.traffic_limit,
        "usage_duration": user.usage_duration,
        "simultaneous_connections": user.simultaneous_connections,
    }

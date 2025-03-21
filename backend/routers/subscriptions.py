from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.models import User
from backend.database.database import get_db

router = APIRouter()

# مسیر نمایش تنظیمات اشتراک
@router.get("/subscription/{user_uuid}")
def get_subscription(user_uuid: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.uuid == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "username": user.username,
        "traffic_limit": user.traffic_limit,
        "usage_duration": user.usage_duration,
        "simultaneous_connections": user.simultaneous_connections,
        "uuid": user.uuid
    }

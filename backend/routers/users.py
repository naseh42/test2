from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models import User  # مدل SQLAlchemy
from backend.database.database import get_db
from backend.schemas import UserResponse, UserCreate, UserUpdate  # اسکیمای Pydantic
import uuid

router = APIRouter()

# دریافت لیست کاربران
@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [user.to_dict() for user in users]

# دریافت جزئیات یک کاربر
@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()

# ایجاد یک کاربر جدید
@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(
        username=user.username,
        uuid=str(uuid.uuid4()),  # تولید UUID به صورت خودکار
        traffic_limit=user.traffic_limit,
        usage_duration=user.usage_duration,
        simultaneous_connections=user.simultaneous_connections
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user.to_dict()

# به‌روزرسانی اطلاعات کاربر
@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user.to_dict()

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# خواندن تنظیمات پایگاه داده از محیط
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")  # پیش‌فرض SQLite

# ایجاد موتور اتصال به پایگاه داده
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# ایجاد SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# پایه برای مدل‌ها
Base = declarative_base()

# Dependency برای استفاده در روترها
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

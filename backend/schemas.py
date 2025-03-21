from pydantic import BaseModel, Field
from typing import Optional

# اسکیمای کاربران
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_.-]+$", description="Username must be alphanumeric and between 3 and 50 characters.")
    uuid: str = Field(..., regex="^[a-f0-9-]{36}$", description="UUID must be in a valid format.")
    traffic_limit: int = Field(..., ge=0, description="Traffic limit in MB.")
    usage_duration: int = Field(..., ge=0, description="Usage duration in minutes.")
    simultaneous_connections: int = Field(..., ge=1, le=10, description="Simultaneous connections allowed.")

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=50)
    traffic_limit: Optional[int] = Field(None, ge=0)
    usage_duration: Optional[int] = Field(None, ge=0)
    simultaneous_connections: Optional[int] = Field(None, ge=1, le=10)

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        orm_mode = True


# اسکیمای دامنه‌ها
class DomainBase(BaseModel):
    name: str = Field(..., max_length=255, description="Domain name.")
    description: Optional[str] = Field(None, max_length=255, description="Domain description.")

class DomainCreate(DomainBase):
    pass

class DomainUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=255)

class DomainResponse(DomainBase):
    id: int
    owner_id: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        orm_mode = True


# اسکیمای تنظیمات
class SettingsBase(BaseModel):
    language: str = Field(..., max_length=10, description="Language setting.")
    theme: str = Field(..., max_length=20, description="Theme setting (e.g., light or dark).")
    enable_notifications: bool = Field(..., description="Enable or disable notifications.")
    preferences: Optional[dict] = Field(None, description="Advanced preferences as JSON.")

class SettingsResponse(SettingsBase):
    id: int
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        orm_mode = True

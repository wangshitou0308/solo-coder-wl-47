from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
from app.models.models import UserRole


class UserCreate(BaseModel):
    username: str
    password: str
    real_name: str
    role: UserRole
    area: Optional[str] = None
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    password: Optional[str] = None
    real_name: Optional[str] = None
    role: Optional[UserRole] = None
    area: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    username: str
    real_name: str
    role: UserRole
    area: Optional[str]
    phone: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

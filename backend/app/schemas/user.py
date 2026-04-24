import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    preferred_language: Optional[str] = None
    response_language: Optional[str] = None


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    is_admin: bool
    avatar_url: Optional[str] = None
    preferred_language: str
    response_language: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[str] = None

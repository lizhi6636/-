from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        if len(v) < 3 or len(v) > 50:
            raise ValueError("用户名长度需在3-50个字符之间")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("密码长度至少6个字符")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    is_verified: bool
    cash: Decimal
    initial_capital: Decimal
    created_at: datetime

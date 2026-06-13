from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse

# Refresh token durations
REFRESH_SHORT_DAYS = 1       # Without "remember me": 1 day
REFRESH_REMEMBER_DAYS = 30   # With "remember me": 30 days


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, data: RegisterRequest) -> User:
        # Check if email or username already exists
        existing = await db.execute(
            select(User).where((User.email == data.email) | (User.username == data.username))
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="邮箱或用户名已被注册",
            )

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用",
            )

        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_delta = timedelta(days=REFRESH_REMEMBER_DAYS) if data.remember_me else timedelta(days=REFRESH_SHORT_DAYS)
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "remember_me": data.remember_me},
            expires_delta=refresh_delta,
        )

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    async def refresh_token(token: str) -> TokenResponse:
        payload = decode_token(token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token无效或已过期",
            )

        user_id = payload.get("sub")
        remember_me = payload.get("remember_me", False)
        access_token = create_access_token(data={"sub": user_id})
        refresh_delta = timedelta(days=REFRESH_REMEMBER_DAYS) if remember_me else timedelta(days=REFRESH_SHORT_DAYS)
        refresh_token = create_refresh_token(
            data={"sub": user_id, "remember_me": remember_me},
            expires_delta=refresh_delta,
        )

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    async def get_me(db: AsyncSession, user: User) -> User:
        return user

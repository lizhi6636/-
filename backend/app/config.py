from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://qtuser:qtpass@localhost:5432/quant_trading"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # JWT
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Trading
    INITIAL_CAPITAL: float = 1_000_000.0
    COMMISSION_RATE: float = 0.00025
    STAMP_TAX_RATE: float = 0.001
    MIN_COMMISSION: float = 5.0

    # App
    ENVIRONMENT: str = "development"
    # Stored as comma-separated string; use .cors_origins property to get as list
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        """Return CORS origins as a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

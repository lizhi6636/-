import uuid
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.position import Position
    from app.models.order import Order


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Trading account
    initial_capital: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=1_000_000.00
    )
    cash: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=1_000_000.00
    )

    # Relationships
    positions: Mapped[list["Position"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    orders: Mapped[list["Order"]] = relationship(
        back_populates="user", lazy="selectin"
    )

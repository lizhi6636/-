import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class Trade(Base, UUIDMixin):
    __tablename__ = "trades"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False)
    stock_name: Mapped[str] = mapped_column(String(50), default="")
    direction: Mapped[str] = mapped_column(String(4), nullable=False)  # "buy" | "sell"
    price: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    commission: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=0)
    stamp_tax: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=0)
    traded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

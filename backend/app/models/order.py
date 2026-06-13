import uuid
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class Order(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "orders"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False)
    stock_name: Mapped[str] = mapped_column(String(50), default="")

    order_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "market" | "limit"
    direction: Mapped[str] = mapped_column(String(4), nullable=False)  # "buy" | "sell"

    limit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 3), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    filled_quantity: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(
        String(15), default="pending"
    )  # "pending" | "partial" | "filled" | "cancelled" | "rejected"

    commission: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=0)
    stamp_tax: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=0)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="orders")

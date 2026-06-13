import uuid
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class Position(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "positions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False)
    stock_name: Mapped[str] = mapped_column(String(50), default="")
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0)
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=0)
    current_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 3), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="positions")

    __table_args__ = (
        UniqueConstraint("user_id", "stock_code", name="uq_user_position_stock"),
    )

import uuid

from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class WatchlistItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "watchlist_items"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False)
    stock_name: Mapped[str] = mapped_column(String(50), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("user_id", "stock_code", name="uq_user_watchlist"),
    )

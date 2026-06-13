import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class AccountSnapshot(Base, UUIDMixin):
    __tablename__ = "account_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    total_asset: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    market_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    daily_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    snapshot_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

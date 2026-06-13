from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class OrderCreate(BaseModel):
    stock_code: str
    direction: str  # "buy" | "sell"
    order_type: str  # "market" | "limit"
    limit_price: Optional[Decimal] = None
    quantity: int

    @model_validator(mode="after")
    def validate_limit_price(self):
        if self.order_type == "limit" and self.limit_price is None:
            raise ValueError("限价单必须指定价格")
        if self.order_type == "market":
            self.limit_price = None
        if self.quantity <= 0:
            raise ValueError("数量必须大于0")
        if self.quantity % 100 != 0:
            raise ValueError("A股交易数量需为100的整数倍(手)")
        if self.direction not in ("buy", "sell"):
            raise ValueError("方向只能是buy或sell")
        if self.order_type not in ("market", "limit"):
            raise ValueError("订单类型只能是market或limit")
        return self


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    stock_code: str
    stock_name: str
    order_type: str
    direction: str
    limit_price: Optional[Decimal] = None
    quantity: int
    filled_quantity: int
    status: str
    commission: Decimal
    stamp_tax: Decimal
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    stock_code: str
    stock_name: str
    direction: str
    price: Decimal
    quantity: int
    commission: Decimal
    stamp_tax: Decimal
    traded_at: datetime


class AccountSummary(BaseModel):
    total_asset: Decimal
    cash: Decimal
    market_value: Decimal
    total_pnl: Decimal
    daily_pnl: Decimal
    initial_capital: Decimal
    total_return_pct: float

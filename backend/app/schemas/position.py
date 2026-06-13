from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stock_code: str
    stock_name: str
    quantity: int
    available_quantity: int
    avg_cost: Decimal
    current_price: Optional[Decimal] = None
    updated_at: datetime

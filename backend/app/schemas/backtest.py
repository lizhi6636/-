from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal


class BacktestCreate(BaseModel):
    name: str
    strategy_code: str
    stock_codes: list[str]
    start_date: date
    end_date: date
    initial_capital: Decimal = Decimal("1000000")
    parameters: dict = {}


class BacktestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    stock_codes: list
    start_date: date
    end_date: date
    initial_capital: Decimal
    status: str
    metrics: Optional[dict] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class BacktestResultResponse(BaseModel):
    task_id: UUID
    status: str
    metrics: Optional[dict] = None
    result_data: Optional[dict] = None
    error_message: Optional[str] = None

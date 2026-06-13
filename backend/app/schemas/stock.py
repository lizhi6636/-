from pydantic import BaseModel
from typing import Optional


class StockKlineRequest(BaseModel):
    period: str = "daily"  # daily, weekly, monthly
    start_date: str
    end_date: str
    adjust: str = "qfq"  # qfq=前复权, hfq=后复权, none=不复权


class StockRealtimeResponse(BaseModel):
    code: str
    name: str
    price: float
    change: float
    change_pct: float
    open: float
    high: float
    low: float
    pre_close: float
    volume: int
    amount: float
    update_time: str


class StockInfoResponse(BaseModel):
    code: str
    name: str
    market: str
    pe: Optional[float] = None
    pb: Optional[float] = None
    market_cap: Optional[float] = None
    total_shares: Optional[int] = None


class IndexDataResponse(BaseModel):
    name: str
    code: str
    price: float
    change: float
    change_pct: float

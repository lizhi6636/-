from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class WatchlistCreate(BaseModel):
    stock_code: str
    stock_name: str = ""
    sort_order: int = 0


class WatchlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stock_code: str
    stock_name: str
    sort_order: int
    created_at: datetime


class DashboardOverview(BaseModel):
    indices: list
    watchlist: list
    account_summary: Optional[dict] = None
    trading_status: dict


class LearnArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    category: str
    summary: str
    tags: list
    view_count: int
    created_at: datetime


class LearnArticleDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    category: str
    content: str
    summary: str
    tags: list
    view_count: int
    created_at: datetime

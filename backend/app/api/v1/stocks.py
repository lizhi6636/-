from fastapi import APIRouter, Query

from app.schemas.stock import StockRealtimeResponse, StockInfoResponse
from app.services.market_data_service import (
    get_kline,
    get_stock_info,
    get_realtime_quote,
    fetch_realtime_from_akshare,
)
from app.utils.stock_links import get_stock_links

router = APIRouter()


@router.get("/{code}")
async def stock_detail(code: str):
    """Get stock basic info + external links."""
    info = await get_stock_info(code)
    links = get_stock_links(code)
    return {"info": info, "links": links}


@router.get("/{code}/kline")
async def stock_kline(
    code: str,
    period: str = Query("daily", description="daily, weekly, monthly"),
    start_date: str = Query("", description="YYYYMMDD"),
    end_date: str = Query("", description="YYYYMMDD"),
    adjust: str = Query("qfq", description="qfq, hfq, or empty"),
):
    """Get K-line (candlestick) data."""
    data = await get_kline(code, period, start_date, end_date, adjust)
    return {"code": code, "period": period, "data": data}


@router.get("/{code}/intraday")
async def stock_intraday(code: str):
    """Get intraday minute data (simplified — uses daily as fallback)."""
    # AKShare intraday data requires specific API endpoints.
    # For simplicity, return latest daily as intraday approximation.
    from datetime import datetime, timedelta
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")
    data = await get_kline(code, "daily", start, end, "qfq")
    return {"code": code, "data": data}


@router.get("/{code}/fundamentals")
async def stock_fundamentals(code: str):
    """Get stock fundamental data."""
    info = await get_stock_info(code)
    return info


@router.get("/{code}/realtime")
async def stock_realtime(code: str):
    """Get real-time quote for a stock."""
    quote = await get_realtime_quote(code)
    if quote is None:
        quote = await fetch_realtime_from_akshare(code)
    return quote or {"code": code, "error": "无法获取实时数据"}


@router.get("/{code}/links")
async def stock_links(code: str):
    """Get external platform links."""
    return get_stock_links(code)

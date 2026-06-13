from fastapi import APIRouter, Query

from app.services.market_data_service import (
    get_index_data,
    get_realtime_quotes,
    fetch_realtime_from_akshare,
)

router = APIRouter()


@router.get("/indices")
async def market_indices():
    """Get major market indices."""
    indices = await get_index_data()
    return {"indices": indices}


@router.get("/quotes")
async def market_quotes(codes: str = Query("", description="Comma-separated stock codes")):
    """Get real-time quotes for multiple stocks."""
    if not codes:
        return {"quotes": {}}

    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    quotes = await get_realtime_quotes(code_list)

    # For missing codes, try to fetch from AKShare
    missing = [c for c in code_list if c not in quotes]
    for code in missing:
        data = await fetch_realtime_from_akshare(code)
        if data:
            quotes[code] = data

    return {"quotes": quotes}


@router.get("/trading-status")
async def trading_status():
    """Get current trading session status."""
    from app.services.trading_clock import session_status
    return session_status()

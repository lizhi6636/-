"""Dashboard service — watchlist CRUD and account overview."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.watchlist_item import WatchlistItem
from app.models.position import Position
from app.models.account_snapshot import AccountSnapshot
from app.schemas.dashboard import WatchlistCreate
from app.services.trading_clock import session_status


async def get_watchlist(db: AsyncSession, user: User) -> list[WatchlistItem]:
    """Get user's watchlist ordered by sort_order."""
    stmt = (
        select(WatchlistItem)
        .where(WatchlistItem.user_id == user.id)
        .order_by(WatchlistItem.sort_order)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add_to_watchlist(
    db: AsyncSession, user: User, data: WatchlistCreate
) -> WatchlistItem:
    """Add a stock to watchlist."""
    item = WatchlistItem(
        user_id=user.id,
        stock_code=data.stock_code,
        stock_name=data.stock_name,
        sort_order=data.sort_order,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def remove_from_watchlist(db: AsyncSession, user: User, watchlist_id: UUID):
    """Remove a stock from watchlist."""
    stmt = delete(WatchlistItem).where(
        WatchlistItem.id == watchlist_id,
        WatchlistItem.user_id == user.id,
    )
    await db.execute(stmt)
    await db.commit()


async def get_account_summary(db: AsyncSession, user: User) -> dict:
    """Calculate account summary including total P&L."""
    # Get positions
    stmt = select(Position).where(Position.user_id == user.id)
    result = await db.execute(stmt)
    positions = list(result.scalars().all())

    # Calculate market value
    market_value = Decimal("0")
    for pos in positions:
        if pos.current_price:
            market_value += Decimal(str(pos.current_price)) * Decimal(pos.quantity)

    total_asset = user.cash + market_value
    total_pnl = total_asset - user.initial_capital
    total_return_pct = (
        float(total_pnl / user.initial_capital * 100)
        if user.initial_capital > 0
        else 0
    )

    # Get today's P&L from latest snapshot
    daily_pnl = Decimal("0")
    stmt = (
        select(AccountSnapshot)
        .where(AccountSnapshot.user_id == user.id)
        .order_by(AccountSnapshot.snapshot_time.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    last_snapshot = result.scalar_one_or_none()
    if last_snapshot:
        daily_pnl = total_asset - last_snapshot.total_asset

    return {
        "total_asset": str(total_asset),
        "cash": str(user.cash),
        "market_value": str(market_value),
        "total_pnl": str(total_pnl),
        "daily_pnl": str(daily_pnl),
        "initial_capital": str(user.initial_capital),
        "total_return_pct": round(total_return_pct, 2),
    }


async def get_dashboard_overview(db: AsyncSession, user: User) -> dict:
    """Get complete dashboard overview data."""
    from app.services.market_data_service import get_index_data, get_realtime_quotes

    # Get indices
    indices = await get_index_data()

    # Get watchlist with real-time quotes
    watchlist = await get_watchlist(db, user)
    watchlist_codes = [w.stock_code for w in watchlist]
    quotes = await get_realtime_quotes(watchlist_codes) if watchlist_codes else {}

    watchlist_data = []
    for item in watchlist:
        quote = quotes.get(item.stock_code, {})
        watchlist_data.append({
            "id": str(item.id),
            "stock_code": item.stock_code,
            "stock_name": item.stock_name,
            "sort_order": item.sort_order,
            "price": quote.get("price", 0),
            "change": quote.get("change", 0),
            "change_pct": quote.get("change_pct", 0),
            "created_at": item.created_at.isoformat(),
        })

    # Get account summary
    account = await get_account_summary(db, user)

    # Get trading status
    trading = session_status()

    return {
        "indices": indices,
        "watchlist": watchlist_data,
        "account_summary": account,
        "trading_status": trading,
    }

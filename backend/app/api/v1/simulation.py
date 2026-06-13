from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.order import Order
from app.models.trade import Trade
from app.models.position import Position
from app.schemas.simulation import (
    OrderCreate,
    OrderResponse,
    TradeResponse,
    AccountSummary,
)
from app.schemas.position import PositionResponse
from app.services.simulation_engine import (
    place_order,
    cancel_order,
    SimulationError,
    MarketClosedError,
)
from app.services.dashboard_service import get_account_summary

router = APIRouter()


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Place a new order (market or limit)."""
    try:
        # Refresh user from DB to get latest cash
        stmt = select(User).where(User.id == current_user.id)
        result = await db.execute(stmt)
        db_user = result.scalar_one()

        order = await place_order(
            db=db,
            user=db_user,
            stock_code=data.stock_code,
            direction=data.direction,
            order_type=data.order_type,
            quantity=data.quantity,
            limit_price=data.limit_price,
        )
        return order
    except SimulationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)


@router.get("/orders", response_model=list[OrderResponse])
async def list_orders(
    status_filter: str = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's orders, optionally filtered by status."""
    stmt = select(Order).where(Order.user_id == current_user.id)
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    stmt = stmt.order_by(Order.created_at.desc()).limit(50)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.delete("/orders/{order_id}")
async def cancel_order_endpoint(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending order."""
    try:
        stmt = select(User).where(User.id == current_user.id)
        result = await db.execute(stmt)
        db_user = result.scalar_one()

        order = await cancel_order(db, db_user, order_id)
        return {"message": "订单已撤销", "order_id": str(order.id)}
    except SimulationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)


@router.get("/positions", response_model=list[PositionResponse])
async def list_positions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's current positions."""
    stmt = select(Position).where(
        Position.user_id == current_user.id,
        Position.quantity > 0,
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/trades", response_model=list[TradeResponse])
async def list_trades(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's trade history."""
    stmt = (
        select(Trade)
        .where(Trade.user_id == current_user.id)
        .order_by(Trade.traded_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/account", response_model=AccountSummary)
async def account_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get account summary."""
    return await get_account_summary(db, current_user)

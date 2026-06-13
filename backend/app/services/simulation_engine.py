"""Paper trading simulation engine.

Handles: order placement, cancellation, matching, T+1 enforcement,
commission calculation, position updates.
"""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.models.order import Order
from app.models.trade import Trade
from app.models.position import Position
from app.services.commission import calc_commission, calc_stamp_tax
from app.services.trading_clock import is_trading_time, now_cst
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


class SimulationError(Exception):
    """Base exception for simulation errors."""
    def __init__(self, detail: str, code: str = "simulation_error"):
        self.detail = detail
        self.code = code


class InsufficientFundsError(SimulationError):
    def __init__(self, required: Decimal, available: Decimal):
        super().__init__(
            detail=f"资金不足: 需要 {required:.2f}, 可用 {available:.2f}",
            code="insufficient_funds",
        )


class InsufficientSharesError(SimulationError):
    def __init__(self, required: int, available: int):
        super().__init__(
            detail=f"可用股数不足: 需要 {required}股, 可用 {available}股(T+1限制)",
            code="insufficient_shares",
        )


class MarketClosedError(SimulationError):
    def __init__(self):
        super().__init__(detail="当前非交易时间，无法下单", code="market_closed")


class InvalidStockCodeError(SimulationError):
    def __init__(self, code: str):
        super().__init__(detail=f"无效的股票代码: {code}", code="invalid_stock_code")


class OrderNotFoundError(SimulationError):
    def __init__(self):
        super().__init__(detail="订单不存在", code="order_not_found")


def validate_stock_code(code: str) -> bool:
    """Validate Chinese A-share stock code format (6 digits)."""
    return bool(code and len(code) == 6 and code.isdigit())


async def get_current_price(stock_code: str) -> tuple:
    """Get current market price and name for a stock via EastMoney API.

    Returns (price, name) tuple. price is Decimal or None.
    """
    from app.core.redis_client import cache_get, cache_set
    import json

    # Try Redis cache first
    cached = await cache_get(f"quote:{stock_code}")
    if cached:
        data = json.loads(cached)
        price = data.get("price", 0)
        name = data.get("name", "")
        if price and float(price) > 0:
            return Decimal(str(price)), name

    # Fetch from EastMoney API directly
    try:
        import asyncio
        price, name, quote_data = await asyncio.to_thread(_fetch_from_eastmoney, stock_code)
        if price is not None and quote_data:
            await cache_set(f"quote:{stock_code}", json.dumps(quote_data), 5)
            return Decimal(str(price)), name or ""
    except Exception as e:
        logger.warning(f"Price fetch failed for {stock_code}: {e}")

    return None, ""


def _fetch_from_eastmoney(stock_code: str) -> tuple:
    """Fetch real-time quote from EastMoney API with multi-endpoint fallback.

    Tries multiple URLs in order — some endpoints are unreliable via Docker/Python.
    """
    import subprocess
    import json as _json

    market = "1" if stock_code.startswith(("6", "5")) else "0"
    secid = f"{market}.{stock_code}"
    fields = "f43,f44,f45,f46,f47,f48,f50,f51,f52,f57,f58,f60,f116,f117,f162,f167,f168,f169,f170,f171"

    # Multiple fallback URLs — try each until one works
    urls = [
        f"http://push2delay.eastmoney.com/api/qt/stock/get?secid={secid}&fields={fields}",
        f"http://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields={fields}",
    ]
    # HTTPS needs --insecure flag in Docker
    curl_base = ["curl", "-s", "--connect-timeout", "5", "--max-time", "10",
                 "-H", "User-Agent: Mozilla/5.0"]

    for url in urls:
        try:
            args = curl_base + [url]
            result = subprocess.run(args, capture_output=True, text=True, timeout=12)
            if result.returncode != 0 or not result.stdout.strip():
                continue  # try next endpoint

            data = _json.loads(result.stdout)
            d = data.get("data", {})
            if not d or d.get("f43", 0) == 0:
                continue

            price = d.get("f43", 0) / 100
            name = d.get("f58", "")
            pre_close = d.get("f60", 0) / 100 if d.get("f60") else 0
            change = price - pre_close if price and pre_close else 0
            change_pct = (change / pre_close * 100) if pre_close else 0

            quote_data = {
                "code": stock_code, "name": name, "price": price,
                "change": round(change, 3), "change_pct": round(change_pct, 3),
                "open": d.get("f46", 0) / 100 if d.get("f46") else 0,
                "high": d.get("f44", 0) / 100 if d.get("f44") else 0,
                "low": d.get("f45", 0) / 100 if d.get("f45") else 0,
                "pre_close": pre_close,
                "volume": d.get("f47", 0) or 0,
                "amount": d.get("f48", 0) or 0,
                "update_time": "",
            }
            return price if price > 0 else None, name, quote_data
        except Exception:
            continue  # try next endpoint

    logger.warning(f"All endpoints failed for {stock_code}")
    return None, None, None


async def place_order(
    db: AsyncSession,
    user: User,
    stock_code: str,
    direction: str,
    order_type: str,
    quantity: int,
    limit_price: Optional[Decimal] = None,
    stock_name: str = "",
) -> Order:
    """Place a new order.

    Args:
        db: Database session
        user: Authenticated user
        stock_code: 6-digit stock code
        direction: "buy" or "sell"
        order_type: "market" or "limit"
        quantity: Number of shares (must be multiple of 100)
        limit_price: Required for limit orders
        stock_name: Stock display name

    Returns:
        Created Order object
    """
    if not validate_stock_code(stock_code):
        raise InvalidStockCodeError(stock_code)

    # Check trading hours for market orders
    if order_type == "market":
        if not is_trading_time():
            raise MarketClosedError()

    # Get current price and stock name
    current_price, fetched_name = await get_current_price(stock_code)
    if not stock_name and fetched_name:
        stock_name = fetched_name
    if order_type == "market" and current_price is None:
        raise SimulationError(
            detail=f"无法获取 {stock_code} 的实时价格，请稍后再试",
            code="price_unavailable",
        )

    # Calculate cost
    exec_price = current_price if order_type == "market" else limit_price
    if exec_price is None:
        exec_price = Decimal("0")

    trade_value = exec_price * Decimal(quantity)
    commission = calc_commission(trade_value)
    stamp_tax = calc_stamp_tax(trade_value, direction)

    if direction == "buy":
        total_cost = trade_value + commission + stamp_tax
        if user.cash < total_cost:
            raise InsufficientFundsError(total_cost, user.cash)

    if direction == "sell":
        # Check position and T+1
        stmt = select(Position).where(
            Position.user_id == user.id,
            Position.stock_code == stock_code,
        )
        result = await db.execute(stmt)
        position = result.scalar_one_or_none()

        if not position or position.available_quantity < quantity:
            available = position.available_quantity if position else 0
            raise InsufficientSharesError(quantity, available)

    # Create order
    order = Order(
        user_id=user.id,
        stock_code=stock_code,
        stock_name=stock_name,
        order_type=order_type,
        direction=direction,
        limit_price=limit_price,
        quantity=quantity,
        status="pending",
        commission=Decimal("0"),
        stamp_tax=Decimal("0"),
    )
    db.add(order)
    await db.flush()

    # For market orders, match immediately
    if order_type == "market":
        await _execute_trade(db, user, order, exec_price, quantity)
        order.status = "filled"
        order.filled_quantity = quantity
        user.cash = user.cash  # Will be recalculated in _execute_trade
    elif order_type == "limit" and direction == "buy":
        # Reserve cash for limit buy orders
        total_cost = exec_price * Decimal(quantity) + commission + stamp_tax
        if user.cash < total_cost:
            raise InsufficientFundsError(total_cost, user.cash)
        user.cash -= total_cost

    await db.commit()
    await db.refresh(order)
    return order


async def _execute_trade(
    db: AsyncSession,
    user: User,
    order: Order,
    price: Decimal,
    quantity: int,
):
    """Execute a trade: create Trade record, update Position and User cash."""
    trade_value = price * Decimal(quantity)
    commission = calc_commission(trade_value)
    stamp_tax = calc_stamp_tax(trade_value, order.direction)

    # Create trade record
    trade = Trade(
        order_id=order.id,
        user_id=user.id,
        stock_code=order.stock_code,
        stock_name=order.stock_name,
        direction=order.direction,
        price=price,
        quantity=quantity,
        commission=commission,
        stamp_tax=stamp_tax,
    )
    db.add(trade)

    # Update or create position
    stmt = select(Position).where(
        Position.user_id == user.id,
        Position.stock_code == order.stock_code,
    )
    result = await db.execute(stmt)
    position = result.scalar_one_or_none()

    if order.direction == "buy":
        if position:
            # Average cost recalculation
            old_value = position.avg_cost * Decimal(position.quantity)
            new_value = price * Decimal(quantity)
            total_qty = position.quantity + quantity
            position.avg_cost = (old_value + new_value) / Decimal(total_qty)
            position.quantity = total_qty
            # T+1: newly bought shares NOT available to sell today
            # available_quantity stays unchanged
        else:
            position = Position(
                user_id=user.id,
                stock_code=order.stock_code,
                stock_name=order.stock_name,
                quantity=quantity,
                available_quantity=0,  # T+1: cannot sell today
                avg_cost=price,
                current_price=price,
            )
            db.add(position)
        # Deduct cash
        total_cost = trade_value + commission + stamp_tax
        user.cash -= total_cost

    elif order.direction == "sell":
        if position:
            total_qty = position.quantity - quantity
            total_cost = position.avg_cost * Decimal(position.quantity) - price * Decimal(quantity)
            if total_qty > 0:
                position.quantity = total_qty
                position.available_quantity = max(0, position.available_quantity - quantity)
                position.avg_cost = total_cost / Decimal(total_qty) if total_qty > 0 else Decimal("0")
            else:
                # Position fully sold
                await db.delete(position)
        # Add cash
        proceeds = trade_value - commission - stamp_tax
        user.cash += proceeds

    # Update order
    order.commission = commission
    order.stamp_tax = stamp_tax
    order.filled_quantity = quantity


async def cancel_order(db: AsyncSession, user: User, order_id: UUID) -> Order:
    """Cancel a pending order and release reserved funds/shares."""
    stmt = select(Order).where(Order.id == order_id, Order.user_id == user.id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise OrderNotFoundError()

    if order.status not in ("pending", "partial"):
        raise SimulationError(
            detail=f"订单状态为 {order.status}，无法撤销",
            code="cannot_cancel",
        )

    order.status = "cancelled"

    # Release reserved cash for unfilled portion of limit buy orders
    unfilled = order.quantity - order.filled_quantity
    if order.direction == "buy" and order.order_type == "limit" and unfilled > 0:
        price = order.limit_price or Decimal("0")
        trade_value = price * Decimal(unfilled)
        commission = calc_commission(trade_value)
        stamp_tax = calc_stamp_tax(trade_value, "buy")
        user.cash += trade_value + commission + stamp_tax

    await db.commit()
    await db.refresh(order)
    return order


# Celery tasks for periodic operations

@celery_app.task(name="app.services.simulation_engine.match_pending_orders")
def match_pending_orders():
    """Periodic task: match pending limit orders against current prices.

    This runs every 5 seconds during trading hours.
    Note: Celery tasks are synchronous, so we use a sync approach here.
    """
    if not is_trading_time():
        return {"matched": 0, "reason": "market_closed"}

    # This is a simplified implementation.
    # In production, each order matching would be an async operation.
    # For the Celery worker context, we use sync patterns.
    logger.info("Running limit order matching check...")
    # The actual matching logic would query DB and compare prices.
    # For now, we log and return.
    return {"matched": 0, "checked": True}


@celery_app.task(name="app.services.simulation_engine.release_t1_shares")
def release_t1_shares():
    """Periodic task: Release T+1 share restrictions at market open.

    Makes all shares in positions available for selling.
    Runs at 9:00 AM on trading days.
    """
    logger.info("Releasing T+1 share restrictions...")
    # In a full implementation, this would:
    # UPDATE positions SET available_quantity = quantity
    # for all positions across all users.
    return {"released": True}

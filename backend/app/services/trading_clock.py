from datetime import datetime, time, timedelta, timezone
from enum import Enum
from app.utils.holidays import is_holiday

# China market hours (Beijing time UTC+8)
CST = timezone(timedelta(hours=8))

MORNING_START = time(9, 30)
MORNING_END = time(11, 30)
AFTERNOON_START = time(13, 0)
AFTERNOON_END = time(15, 0)


class SessionStatus(str, Enum):
    PRE_OPEN = "pre_open"      # Before 9:30
    MORNING = "morning"        # 9:30-11:30
    LUNCH = "lunch"            # 11:30-13:00
    AFTERNOON = "afternoon"    # 13:00-15:00
    CLOSED = "closed"          # After 15:00
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


def now_cst() -> datetime:
    return datetime.now(CST)


def is_weekend(dt: datetime) -> bool:
    return dt.weekday() >= 5  # 5=Saturday, 6=Sunday


def is_trading_time(dt: datetime = None) -> bool:
    """Check if trading is currently active for order matching."""
    if dt is None:
        dt = now_cst()
    if is_weekend(dt) or is_holiday(dt):
        return False
    t = dt.time()
    return (MORNING_START <= t <= MORNING_END) or (AFTERNOON_START <= t <= AFTERNOON_END)


def session_status(dt: datetime = None) -> dict:
    """Get current trading session status with details."""
    if dt is None:
        dt = now_cst()

    if is_weekend(dt):
        next_open = next_trading_day(dt)
        return {
            "status": SessionStatus.WEEKEND.value,
            "is_trading": False,
            "next_open": next_open.replace(hour=9, minute=30).isoformat(),
            "message": "周末休市",
        }

    if is_holiday(dt):
        next_open = next_trading_day(dt)
        return {
            "status": SessionStatus.HOLIDAY.value,
            "is_trading": False,
            "next_open": next_open.replace(hour=9, minute=30).isoformat(),
            "message": "节假日休市",
        }

    t = dt.time()
    if t < MORNING_START:
        return {
            "status": SessionStatus.PRE_OPEN.value,
            "is_trading": False,
            "next_open": dt.replace(hour=9, minute=30, second=0).isoformat(),
            "message": "盘前，距开盘还有一段时间",
        }
    elif MORNING_START <= t <= MORNING_END:
        return {
            "status": SessionStatus.MORNING.value,
            "is_trading": True,
            "next_close": dt.replace(hour=11, minute=30, second=0).isoformat(),
            "message": "交易中（上午盘）",
        }
    elif t < AFTERNOON_START:
        return {
            "status": SessionStatus.LUNCH.value,
            "is_trading": False,
            "next_open": dt.replace(hour=13, minute=0, second=0).isoformat(),
            "message": "午间休市",
        }
    elif AFTERNOON_START <= t <= AFTERNOON_END:
        return {
            "status": SessionStatus.AFTERNOON.value,
            "is_trading": True,
            "next_close": dt.replace(hour=15, minute=0, second=0).isoformat(),
            "message": "交易中（下午盘）",
        }
    else:
        next_open = next_trading_day(dt + timedelta(days=1))
        return {
            "status": SessionStatus.CLOSED.value,
            "is_trading": False,
            "next_open": next_open.replace(hour=9, minute=30).isoformat(),
            "message": "已收盘",
        }


def next_trading_day(dt: datetime) -> datetime:
    """Find the next trading day."""
    next_day = dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    while is_weekend(next_day) or is_holiday(next_day):
        next_day += timedelta(days=1)
    return next_day

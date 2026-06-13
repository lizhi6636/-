from decimal import Decimal
from app.config import settings


def calc_commission(trade_value: Decimal) -> Decimal:
    """Calculate trading commission.

    Rate: commission_rate (default 0.025%) of trade value.
    Minimum: min_commission (default 5 CNY).
    """
    commission = trade_value * Decimal(str(settings.COMMISSION_RATE))
    min_commission = Decimal(str(settings.MIN_COMMISSION))
    return max(commission, min_commission)


def calc_stamp_tax(trade_value: Decimal, direction: str) -> Decimal:
    """Calculate stamp tax.

    Rate: stamp_tax_rate (default 0.1%) on sell side only.
    """
    if direction == "sell":
        return trade_value * Decimal(str(settings.STAMP_TAX_RATE))
    return Decimal("0")


def calc_total_cost(price: Decimal, quantity: int, direction: str) -> Decimal:
    """Calculate total cost including commission and stamp tax."""
    trade_value = price * Decimal(quantity)
    commission = calc_commission(trade_value)
    stamp_tax = calc_stamp_tax(trade_value, direction)
    return trade_value + commission + stamp_tax

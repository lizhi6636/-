"""China A-share market holiday calendar.

This is a simplified version. In production, use akshare to fetch the
official holiday calendar from SSE/SZSE.
"""

from datetime import datetime, date
from typing import Set

# Known holidays for 2026 (tentative, based on typical schedule)
# In production this should be fetched from an API or updated annually
_HOLIDAYS_2026: Set[date] = {
    # New Year
    date(2026, 1, 1),
    date(2026, 1, 2),
    # Chinese New Year (around Feb 17, 2026)
    date(2026, 2, 16), date(2026, 2, 17), date(2026, 2, 18),
    date(2026, 2, 19), date(2026, 2, 20),
    # Qingming
    date(2026, 4, 5), date(2026, 4, 6),
    # Labor Day
    date(2026, 5, 1), date(2026, 5, 4), date(2026, 5, 5),
    # Dragon Boat
    date(2026, 6, 19),
    # Mid-Autumn + National Day (around Oct 2026)
    date(2026, 9, 25),
    date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 5),
    date(2026, 10, 6), date(2026, 10, 7), date(2026, 10, 8),
}

# Cache for quick lookup
_ALL_HOLIDAYS: Set[date] = set(_HOLIDAYS_2026)


def is_holiday(dt: datetime) -> bool:
    """Check if the given datetime falls on a China market holiday."""
    return dt.date() in _ALL_HOLIDAYS


def add_holiday(d: date):
    """Add a holiday to the calendar."""
    _ALL_HOLIDAYS.add(d)


def get_holidays() -> Set[date]:
    """Get all known holidays."""
    return set(_ALL_HOLIDAYS)

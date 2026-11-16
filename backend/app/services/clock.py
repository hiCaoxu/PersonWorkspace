"""统一时区的时间入口，避免各处自行取 now() 导致跨日不一致。"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings

TZ = ZoneInfo(settings.timezone)


def now() -> datetime:
    return datetime.now(TZ)


def today() -> date:
    return now().date()


def day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, datetime.min.time(), tzinfo=TZ)
    return start, start + timedelta(days=1)


def week_bounds(day: date) -> tuple[date, date]:
    """以周一为周首，返回本周一与周日。"""
    monday = day - timedelta(days=day.weekday())
    return monday, monday + timedelta(days=6)


def month_bounds(day: date) -> tuple[date, date]:
    import calendar

    last = calendar.monthrange(day.year, day.month)[1]
    return date(day.year, day.month, 1), date(day.year, day.month, last)


def shift_month(day: date, delta: int) -> date:
    total = day.year * 12 + (day.month - 1) + delta
    year, month = divmod(total, 12)
    return date(year, month + 1, 1)

"""循环待办：由基础日期与规则推算下一次到期日。"""

import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta

FREQUENCIES = ("none", "daily", "weekly", "monthly", "yearly")


class RecurrenceError(ValueError):
    pass


@dataclass(frozen=True)
class RecurrenceRule:
    frequency: str = "none"
    interval: int = 1
    weekdays: tuple[int, ...] = field(default_factory=tuple)
    until: date | None = None

    def __post_init__(self) -> None:
        if self.frequency not in FREQUENCIES:
            raise RecurrenceError(f"未知循环频率: {self.frequency}")
        if self.interval < 1:
            raise RecurrenceError("循环间隔必须 >= 1")
        for wd in self.weekdays:
            if not 0 <= wd <= 6:
                raise RecurrenceError("星期取值必须在 0-6 之间")


def add_months(d: date, months: int) -> date:
    """加月，月末自动收敛（1/31 + 1月 -> 2/28 或 2/29）。"""
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


def next_occurrence(base: date, rule: RecurrenceRule) -> date | None:
    """返回下一次到期日；不循环或已超过 until 时返回 None。"""
    if rule.frequency == "none":
        return None

    if rule.frequency == "daily":
        nxt = base + timedelta(days=rule.interval)
    elif rule.frequency == "weekly":
        if rule.weekdays:
            # 指定了星期几：取相对 base 的下一个匹配日（真正的下一周，偏移 1-7 天）
            offsets = sorted(((wd - base.weekday()) % 7) or 7 for wd in rule.weekdays)
            candidates = [base + timedelta(days=off) for off in offsets]
            nxt = min(candidates)
            if rule.interval > 1:
                nxt = nxt + timedelta(weeks=rule.interval - 1)
        else:
            nxt = base + timedelta(weeks=rule.interval)
    elif rule.frequency == "monthly":
        nxt = add_months(base, rule.interval)
    else:  # yearly
        nxt = add_months(base, 12 * rule.interval)

    if rule.until is not None and nxt > rule.until:
        return None
    return nxt


def should_rollover(rule: RecurrenceRule, completed_on: date, current_due: date) -> bool:
    """完成当天是否该生成下一实例：仅当到期日已到或已过。"""
    return rule.frequency != "none" and current_due <= completed_on

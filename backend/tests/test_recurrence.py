"""循环规则：下次到期日计算与边界收敛。"""

from datetime import date

import pytest

from app.services.recurrence import (
    RecurrenceError,
    RecurrenceRule,
    add_months,
    next_occurrence,
    should_rollover,
)


def test_none_frequency_returns_none():
    assert next_occurrence(date(2026, 11, 15), RecurrenceRule("none")) is None


def test_daily_with_interval():
    rule = RecurrenceRule("daily", interval=3)
    assert next_occurrence(date(2026, 11, 15), rule) == date(2026, 11, 18)


def test_weekly_without_weekdays():
    rule = RecurrenceRule("weekly", interval=2)
    assert next_occurrence(date(2026, 11, 15), rule) == date(2026, 11, 29)


def test_weekly_with_weekdays_picks_next_match():
    # 2026-11-15 是周日(6)，规则为每周一(0)与周四(3) -> 最近的是周一 11-16
    rule = RecurrenceRule("weekly", weekdays=(0, 3))
    assert next_occurrence(date(2026, 11, 15), rule) == date(2026, 11, 16)


def test_weekly_weekdays_never_returns_same_day():
    rule = RecurrenceRule("weekly", weekdays=(6,))
    nxt = next_occurrence(date(2026, 11, 15), rule)
    assert nxt == date(2026, 11, 22)
    assert nxt > date(2026, 11, 15)


@pytest.mark.parametrize(
    ("base", "months", "expected"),
    [
        (date(2026, 1, 31), 1, date(2026, 2, 28)),
        (date(2024, 1, 31), 1, date(2024, 2, 29)),
        (date(2026, 3, 31), 1, date(2026, 4, 30)),
        (date(2026, 11, 15), 3, date(2027, 2, 15)),
        (date(2026, 12, 15), 1, date(2027, 1, 15)),
    ],
)
def test_add_months_clamps_to_month_end(base, months, expected):
    assert add_months(base, months) == expected


def test_monthly_rollover_from_jan_31():
    rule = RecurrenceRule("monthly")
    assert next_occurrence(date(2026, 1, 31), rule) == date(2026, 2, 28)


def test_yearly_rollover_from_leap_day():
    rule = RecurrenceRule("yearly")
    assert next_occurrence(date(2024, 2, 29), rule) == date(2025, 2, 28)


def test_until_cuts_off():
    rule = RecurrenceRule("daily", interval=1, until=date(2026, 11, 16))
    assert next_occurrence(date(2026, 11, 15), rule) == date(2026, 11, 16)
    assert next_occurrence(date(2026, 11, 16), rule) is None


def test_invalid_frequency_raises():
    with pytest.raises(RecurrenceError):
        RecurrenceRule("hourly")


def test_invalid_interval_raises():
    with pytest.raises(RecurrenceError):
        RecurrenceRule("daily", interval=0)


def test_invalid_weekday_raises():
    with pytest.raises(RecurrenceError):
        RecurrenceRule("weekly", weekdays=(7,))


def test_should_rollover_only_when_due():
    rule = RecurrenceRule("daily")
    assert should_rollover(rule, date(2026, 11, 15), date(2026, 11, 15)) is True
    assert should_rollover(rule, date(2026, 11, 15), date(2026, 11, 20)) is False
    assert should_rollover(RecurrenceRule("none"), date(2026, 11, 15), date(2026, 11, 15)) is False

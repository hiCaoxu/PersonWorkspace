"""日记标题：ISO 8601 周算法的硬性断言。"""

from datetime import date

import pytest

from app.services.diary_title import (
    format_diary_title,
    iso_week_number,
    iso_week_year,
    weekday_cn,
)


def test_2026_11_15_is_iso_week_46():
    assert iso_week_number(date(2026, 11, 15)) == 46


def test_title_matches_required_format():
    # 需求给定样例，采用 ISO 周后周数为 46
    assert format_diary_title(date(2026, 11, 15)) == "2026年11月15日 46周星期日"


def test_no_leading_zero():
    assert format_diary_title(date(2026, 1, 1)) == "2026年1月1日 1周星期四"


@pytest.mark.parametrize(
    ("day", "expected_week", "expected_weekday"),
    [
        (date(2026, 1, 1), 1, "星期四"),
        (date(2026, 1, 4), 1, "星期日"),
        (date(2026, 1, 5), 2, "星期一"),
        (date(2026, 11, 9), 46, "星期一"),
        (date(2026, 11, 15), 46, "星期日"),
        (date(2026, 12, 31), 53, "星期四"),
    ],
)
def test_week_and_weekday(day, expected_week, expected_weekday):
    assert iso_week_number(day) == expected_week
    assert weekday_cn(day) == expected_weekday


def test_cross_year_boundary_uses_iso_week_year():
    # 2027-01-01 属于 2026-W53，但标题年份取公历年
    d = date(2027, 1, 1)
    assert iso_week_year(d) == 2026
    assert iso_week_number(d) == 53
    assert format_diary_title(d) == "2027年1月1日 53周星期五"


def test_previous_year_week_53():
    d = date(2021, 1, 1)
    assert iso_week_year(d) == 2020
    assert format_diary_title(d) == "2021年1月1日 53周星期五"


def test_leap_day():
    d = date(2024, 2, 29)
    assert format_diary_title(d) == "2024年2月29日 9周星期四"


def test_week_number_range_is_valid():
    for month in range(1, 13):
        for day in (1, 15, 28):
            assert 1 <= iso_week_number(date(2026, month, day)) <= 53


def test_title_has_no_time_component():
    title = format_diary_title(date(2026, 11, 15))
    assert ":" not in title
    assert title.count("周") == 1

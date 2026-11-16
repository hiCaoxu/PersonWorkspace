"""农历换算：全部与 lunar-python 结果互为校验，不硬编码猜测值。"""

from datetime import date

import pytest

from app.services.lunar import (
    age_by_lunar,
    constellation,
    lunar_text,
    lunar_to_solar,
    next_lunar_birthday,
    solar_to_lunar,
    zodiac,
)


def test_lunar_to_solar_roundtrip_for_real_birthday():
    # 真实生日：农历 1992 年 2 月 29 日
    solar_date = lunar_to_solar(1992, 2, 29)
    lunar = solar_to_lunar(solar_date)
    assert lunar.getMonth() == 2
    assert lunar.getDay() == 29
    assert lunar.getYear() == 1992


def test_real_birthday_is_after_id_card_birthday():
    # 证件登记 1992-02-05，真实农历生日换算后应晚于它
    solar_date = lunar_to_solar(1992, 2, 29)
    assert solar_date > date(1992, 2, 5)
    assert solar_date < date(1992, 6, 1)


def test_zodiac_is_monkey():
    assert zodiac(lunar_to_solar(1992, 2, 29)) == "猴"


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(1992, 4, 2), "白羊"),
        (date(2026, 11, 15), "天蝎"),
        (date(2026, 1, 1), "摩羯"),
    ],
)
def test_constellation(day, expected):
    assert constellation(day).startswith(expected)


def test_lunar_text_contains_month_and_day():
    text = lunar_text(lunar_to_solar(1992, 2, 29))
    assert text.startswith("农历")
    assert "二月" in text
    assert "廿九" in text


def test_lunar_text_without_year():
    text = lunar_text(lunar_to_solar(1992, 2, 29), with_year=False)
    assert "二月廿九" == text


def test_next_lunar_birthday_maps_back_to_lunar_date():
    today = date(2026, 11, 15)
    nxt = next_lunar_birthday(2, 29, today)
    assert nxt >= today
    lunar = solar_to_lunar(nxt)
    assert lunar.getMonth() == 2
    assert lunar.getDay() == 29
    assert nxt.year in (2027, 2028)


def test_next_lunar_birthday_includes_today():
    today = lunar_to_solar(2027, 2, 29)
    assert next_lunar_birthday(2, 29, today) == today


def test_invalid_lunar_month_rejected():
    with pytest.raises(ValueError):
        lunar_to_solar(1992, 13, 1)


def test_invalid_lunar_day_rejected():
    with pytest.raises(ValueError):
        lunar_to_solar(1992, 2, 31)


def test_age_by_lunar_counts_before_birthday():
    birth = lunar_to_solar(1992, 2, 29)
    # 2027 年生日前（1 月）应为 34 岁
    assert age_by_lunar(birth, date(2027, 1, 10), 2, 29) == 34
    # 生日后应为 35 岁
    after = lunar_to_solar(2027, 2, 29)
    assert age_by_lunar(birth, after, 2, 29) == 35

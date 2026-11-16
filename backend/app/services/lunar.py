"""农历换算：全部交由 lunar-python 计算，禁止硬编码换算结果。"""

from datetime import date

from lunar_python import Lunar, Solar

# 闰月用负数表示（lunar-python 约定），此处仅处理正月到腊月
LUNAR_MONTH_MAX = 12


def _solar_date(solar: Solar) -> date:
    return date(solar.getYear(), solar.getMonth(), solar.getDay())


def lunar_to_solar(year: int, month: int, day: int) -> date:
    """农历 -> 公历。month 为正表示非闰月。"""
    if not 1 <= month <= LUNAR_MONTH_MAX:
        raise ValueError(f"农历月份超出范围: {month}")
    if not 1 <= day <= 30:
        raise ValueError(f"农历日期超出范围: {day}")
    return _solar_date(Lunar.fromYmd(year, month, day).getSolar())


def solar_to_lunar(d: date) -> Lunar:
    return Solar.fromYmd(d.year, d.month, d.day).getLunar()


def lunar_text(d: date, with_year: bool = True) -> str:
    """如「农历二〇二六年十月初七」；with_year=False 时仅「十月初七」。"""
    lunar = solar_to_lunar(d)
    body = f"{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}"
    return f"农历{lunar.getYearInChinese()}年{body}" if with_year else body


def zodiac(d: date) -> str:
    """生肖，按农历年。"""
    return solar_to_lunar(d).getYearShengXiao()


def constellation(d: date) -> str:
    return Solar.fromYmd(d.year, d.month, d.day).getXingZuo()


def next_lunar_birthday(month: int, day: int, today: date) -> date:
    """按农历每年重算下一次生日（含今天）。"""
    for year in (today.year, today.year + 1):
        try:
            candidate = lunar_to_solar(year, month, day)
        except (ValueError, IndexError):
            # 该年该农历月不足 30 天时收敛到当月最后一天
            candidate = lunar_to_solar(year, month, 29)
        if candidate >= today:
            return candidate
    raise RuntimeError("无法计算下一次农历生日")


def age_by_lunar(birth_solar: date, today: date, month: int, day: int) -> int:
    """按农历生日计算周岁。"""
    years = today.year - birth_solar.year
    this_year_birthday = next_lunar_birthday(month, day, date(today.year, 1, 1))
    if today < this_year_birthday:
        years -= 1
    return max(years, 0)

"""日记标题：ISO 8601 周算法的唯一口径。

前端不得重复实现，只渲染后端返回值。
格式：{公历年}年{M}月{D}日 {ISO周}周{星期X}
示例：2026-11-15 -> 2026年11月15日 46周星期日
"""

from datetime import date

WEEKDAY_CN = (
    "星期一",
    "星期二",
    "星期三",
    "星期四",
    "星期五",
    "星期六",
    "星期日",
)


def iso_week_number(d: date) -> int:
    """ISO 8601 周号：周一为周首，年初不完整周归入上一年。"""
    return d.isocalendar()[1]


def iso_week_year(d: date) -> int:
    """ISO 周年，跨年时可能与公历年不同（如 2027-01-01 属 2026-W53）。"""
    return d.isocalendar()[0]


def weekday_cn(d: date) -> str:
    return WEEKDAY_CN[d.weekday()]


def format_diary_title(d: date) -> str:
    # 年份取日期自身的公历年，周号取 ISO 周号
    return f"{d.year}年{d.month}月{d.day}日 {iso_week_number(d)}周{weekday_cn(d)}"

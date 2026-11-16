"""公共元信息：农历、星期与 ISO 周，供日期选择器等处展示。"""

from datetime import date

from fastapi import APIRouter

from app.core.deps import OwnerDep
from app.services.diary_title import format_diary_title, iso_week_number, weekday_cn
from app.services.lunar import lunar_text, zodiac

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/lunar")
async def lunar_info(day: date, owner: OwnerDep) -> dict:
    return {
        "date": day.isoformat(),
        "lunar": lunar_text(day, with_year=False),
        "lunar_full": lunar_text(day),
        "weekday": weekday_cn(day),
        "iso_week": iso_week_number(day),
        "title": format_diary_title(day),
        "zodiac": zodiac(day),
    }


@router.get("/lunar/batch")
async def lunar_batch(days: str, owner: OwnerDep) -> dict:
    """批量换算，供列表一次取回多天农历，避免逐行请求。"""
    result: dict[str, str] = {}
    for raw in days.split(","):
        value = raw.strip()
        if not value or value in result:
            continue
        try:
            current = date.fromisoformat(value)
        except ValueError:
            continue
        result[value] = lunar_text(current, with_year=False)
    return {"items": result}

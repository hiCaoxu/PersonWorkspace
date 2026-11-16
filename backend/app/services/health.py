"""健康数据汇总：一律基于记录表聚合，不吃入已删除数据。"""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.health import HealthDiet, HealthExercise, HealthSleep, HealthWeight

ZERO = Decimal("0")


def _dec(value) -> Decimal:
    return Decimal(str(value if value is not None else 0))


def _q2(value) -> Decimal:
    return _dec(value).quantize(Decimal("0.01"))


def _q1(value) -> Decimal:
    return _dec(value).quantize(Decimal("0.1"))


def _range(column, start: date, end: date):
    return (column >= start, column <= end)


async def diet_summary(session: AsyncSession, start: date, end: date) -> dict:
    total, count = (
        await session.execute(
            select(
                func.coalesce(func.sum(HealthDiet.calories_kcal), 0),
                func.count(HealthDiet.id),
            ).where(HealthDiet.deleted_at.is_(None), *_range(HealthDiet.record_date, start, end))
        )
    ).one()

    meals = (
        await session.execute(
            select(
                HealthDiet.meal,
                func.coalesce(func.sum(HealthDiet.calories_kcal), 0),
                func.count(HealthDiet.id),
            )
            .where(HealthDiet.deleted_at.is_(None), *_range(HealthDiet.record_date, start, end))
            .group_by(HealthDiet.meal)
        )
    ).all()

    days = (end - start).days + 1
    return {
        "total_kcal": _q1(total),
        "record_count": int(count),
        "avg_kcal_per_day": _q1(_dec(total) / days) if days > 0 else ZERO,
        "by_meal": {meal: {"kcal": _q1(kcal), "count": int(cnt)} for meal, kcal, cnt in meals},
    }


async def weight_trend(session: AsyncSession, start: date, end: date) -> list[dict]:
    rows = (
        await session.execute(
            select(HealthWeight.record_date, HealthWeight.weight_kg, HealthWeight.body_fat_pct)
            .where(HealthWeight.deleted_at.is_(None), *_range(HealthWeight.record_date, start, end))
            .order_by(HealthWeight.record_date.asc())
        )
    ).all()
    return [
        {
            "date": d,
            "weight_kg": _q2(w),
            "body_fat_pct": _q1(f) if f is not None else None,
        }
        for d, w, f in rows
    ]


async def exercise_summary(session: AsyncSession, start: date, end: date) -> dict:
    total_min, count, total_kcal = (
        await session.execute(
            select(
                func.coalesce(func.sum(HealthExercise.duration_min), 0),
                func.count(HealthExercise.id),
                func.coalesce(func.sum(HealthExercise.calories), 0),
            ).where(HealthExercise.deleted_at.is_(None), *_range(HealthExercise.record_date, start, end))
        )
    ).one()
    return {
        "total_minutes": int(total_min),
        "record_count": int(count),
        "total_kcal": _q1(total_kcal),
    }


async def sleep_summary(session: AsyncSession, start: date, end: date) -> dict:
    avg_min, total_min, count, avg_quality = (
        await session.execute(
            select(
                func.coalesce(func.avg(HealthSleep.duration_min), 0),
                func.coalesce(func.sum(HealthSleep.duration_min), 0),
                func.count(HealthSleep.id),
                func.coalesce(func.avg(HealthSleep.quality), 0),
            ).where(HealthSleep.deleted_at.is_(None), *_range(HealthSleep.record_date, start, end))
        )
    ).one()
    return {
        "avg_minutes": int(Decimal(str(avg_min)).quantize(Decimal("1"))),
        "total_minutes": int(total_min),
        "record_count": int(count),
        "avg_quality": _q1(avg_quality),
    }


async def overview(session: AsyncSession, day: date) -> dict:
    diet = await diet_summary(session, day, day)
    exercise = await exercise_summary(session, day, day)
    sleep = await sleep_summary(session, day, day)
    weights = await weight_trend(session, day, day)
    return {
        "date": day,
        "kcal_today": diet["total_kcal"],
        "exercise_minutes": exercise["total_minutes"],
        "sleep_minutes": sleep["avg_minutes"],
        "weight_kg": weights[-1]["weight_kg"] if weights else None,
    }

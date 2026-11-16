"""首页聚合：跨模块只读拼装，单请求内并行查询。"""

import asyncio
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.note import Note
from app.models.todo import Todo
from app.services import finance as finance_service
from app.services.clock import month_bounds, today, week_bounds
from app.services.lunar import lunar_text, zodiac


async def _todos_between(session: AsyncSession, start: date, end: date, limit: int = 8) -> list[Todo]:
    stmt = (
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(
            Todo.deleted_at.is_(None),
            Todo.done.is_(False),
            Todo.due_date.is_not(None),
            Todo.due_date >= start,
            Todo.due_date <= end,
        )
        .order_by(Todo.system_key.is_(None).asc(), Todo.sort_order.asc(), Todo.due_date.asc(), Todo.id.asc())
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().unique().all())


async def random_note(session: AsyncSession) -> Note | None:
    stmt = (
        select(Note)
        .options(selectinload(Note.tags))
        .where(Note.deleted_at.is_(None))
        .order_by(func.random())
        .limit(1)
    )
    return (await session.execute(stmt)).scalars().unique().first()


async def build_dashboard(session: AsyncSession, day: date | None = None) -> dict:
    current = day or today()
    month_start, month_end = month_bounds(current)
    week_start, week_end = week_bounds(current)

    income_expense, assets, today_todos, week_todos, note = await asyncio.gather(
        finance_service.period_income_expense(session, month_start, month_end),
        finance_service.total_assets(session),
        _todos_between(session, current, current),
        _todos_between(session, week_start, week_end, limit=12),
        random_note(session),
    )

    return {
        "date": current,
        "lunar": lunar_text(current, with_year=False),
        "zodiac": zodiac(current),
        "month_income": income_expense["income"],
        "month_expense": income_expense["expense"],
        "total_assets": assets,
        "today_todos": today_todos,
        "week_todos": week_todos,
        "random_note": note,
    }


def week_span_label(day: date) -> str:
    start, end = week_bounds(day)
    return f"{start.month}月{start.day}日 - {end.month}月{end.day}日"


def next_seven_days(day: date) -> list[date]:
    return [day + timedelta(days=i) for i in range(7)]

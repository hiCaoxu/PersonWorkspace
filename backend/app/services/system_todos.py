"""每日系统待办：记账 / 锻炼 / 饮食。

幂等由部分唯一索引 uq_todo_system_day 保证，写入统一走 ON CONFLICT DO NOTHING。
"""

import enum
from datetime import date, datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.todo import Todo


class SystemKey(str, enum.Enum):
    FINANCE = "finance"
    EXERCISE = "exercise"
    DIET = "diet"


# system_key -> (标题, 描述, 排序)
SYSTEM_TODO_META: dict[SystemKey, tuple[str, str, int]] = {
    SystemKey.FINANCE: ("记账", "记录今天的收入与支出", 10),
    SystemKey.EXERCISE: ("锻炼", "记录今天的运动", 20),
    SystemKey.DIET: ("饮食", "记录今天的饮食与热量", 30),
}

_CONFLICT_WHERE = text("system_key IS NOT NULL AND deleted_at IS NULL")


async def list_today_system_todos(session: AsyncSession, day: date) -> list[Todo]:
    stmt = (
        select(Todo)
        .where(
            Todo.system_key.is_not(None),
            Todo.due_date == day,
            Todo.deleted_at.is_(None),
        )
        .order_by(Todo.sort_order, Todo.id)
    )
    return list((await session.execute(stmt)).scalars().all())


async def ensure_today_system_todos(
    session: AsyncSession, day: date, enabled: bool = True
) -> list[Todo]:
    """生成当天三条系统待办，重复调用不会重复创建。"""
    if enabled:
        for key, (title, description, sort_order) in SYSTEM_TODO_META.items():
            stmt = (
                pg_insert(Todo)
                .values(
                    title=title,
                    description=description,
                    due_date=day,
                    done=False,
                    system_key=key.value,
                    frequency="none",
                    interval=1,
                    sort_order=sort_order,
                )
                .on_conflict_do_nothing(
                    index_elements=["system_key", "due_date"],
                    index_where=_CONFLICT_WHERE,
                )
            )
            await session.execute(stmt)
        await session.flush()
    return await list_today_system_todos(session, day)


async def complete_system_todo(session: AsyncSession, key: SystemKey, day: date) -> bool:
    """录入对应记录后勾选当日系统待办。只置完成，不反向删记录。"""
    stmt = select(Todo).where(
        Todo.system_key == key.value,
        Todo.due_date == day,
        Todo.deleted_at.is_(None),
    )
    todo = (await session.execute(stmt)).scalars().first()
    if todo is None or todo.done:
        return False
    todo.done = True
    todo.completed_at = datetime.now(timezone.utc)
    await session.flush()
    return True

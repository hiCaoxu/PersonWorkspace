"""每日系统待办：幂等、按日隔离、联动勾选。"""

from datetime import date, datetime, timezone

from sqlalchemy import func, select

from app.models.todo import Todo
from app.services.system_todos import (
    SYSTEM_TODO_META,
    SystemKey,
    complete_system_todo,
    ensure_today_system_todos,
    list_today_system_todos,
)

DAY = date(2026, 11, 15)


async def _system_count(db) -> int:
    stmt = select(func.count()).select_from(Todo).where(
        Todo.system_key.is_not(None), Todo.deleted_at.is_(None)
    )
    return int((await db.execute(stmt)).scalar_one())


async def test_creates_three_todos(db):
    todos = await ensure_today_system_todos(db, DAY)
    assert len(todos) == 3
    assert {t.system_key for t in todos} == {"finance", "exercise", "diet"}
    assert {t.title for t in todos} == {"记账", "锻炼", "饮食"}
    assert all(t.due_date == DAY for t in todos)


async def test_idempotent_on_repeat(db):
    await ensure_today_system_todos(db, DAY)
    await ensure_today_system_todos(db, DAY)
    await ensure_today_system_todos(db, DAY)
    assert await _system_count(db) == 3


async def test_each_day_gets_its_own_set(db):
    await ensure_today_system_todos(db, DAY)
    await ensure_today_system_todos(db, date(2026, 11, 16))
    assert await _system_count(db) == 6


async def test_disabled_switch_creates_nothing(db):
    todos = await ensure_today_system_todos(db, DAY, enabled=False)
    assert todos == []
    assert await _system_count(db) == 0


async def test_system_todos_have_no_recurrence(db):
    todos = await ensure_today_system_todos(db, DAY)
    assert all(t.frequency == "none" for t in todos)
    assert all(t.system_key in {k.value for k in SYSTEM_TODO_META} for t in todos)


async def test_complete_system_todo(db):
    await ensure_today_system_todos(db, DAY)
    assert await complete_system_todo(db, SystemKey.DIET, DAY) is True
    todos = {t.system_key: t for t in await list_today_system_todos(db, DAY)}
    assert todos["diet"].done is True
    assert todos["diet"].completed_at is not None
    assert todos["finance"].done is False


async def test_complete_is_idempotent(db):
    await ensure_today_system_todos(db, DAY)
    assert await complete_system_todo(db, SystemKey.FINANCE, DAY) is True
    assert await complete_system_todo(db, SystemKey.FINANCE, DAY) is False


async def test_complete_before_generation_returns_false(db):
    assert await complete_system_todo(db, SystemKey.EXERCISE, DAY) is False


async def test_deleted_system_todo_regenerates(db):
    await ensure_today_system_todos(db, DAY)
    todos = await list_today_system_todos(db, DAY)
    todos[0].deleted_at = datetime.now(timezone.utc)
    await db.flush()

    assert await _system_count(db) == 2
    again = await ensure_today_system_todos(db, DAY)
    assert len(again) == 3
    assert await _system_count(db) == 3

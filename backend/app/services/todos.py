"""待办：查询、增删改、完成与循环实例生成。"""

from datetime import date, datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError, ValidationError
from app.models.tag import Tag
from app.models.todo import Todo
from app.services.clock import today, week_bounds
from app.services.recurrence import RecurrenceRule, next_occurrence

MAX_LIMIT = 200
VIEWS = ("all", "pending", "today", "week", "done")


async def list_todos(
    session: AsyncSession,
    *,
    view: str = "all",
    tag_id: int | None = None,
    q: str | None = None,
    limit: int = MAX_LIMIT,
) -> list[Todo]:
    if view not in VIEWS:
        raise ValidationError(f"未知筛选视图: {view}")
    limit = max(1, min(limit, MAX_LIMIT))

    stmt = (
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(Todo.deleted_at.is_(None))
    )

    current = today()
    if view == "pending":
        stmt = stmt.where(Todo.done.is_(False))
    elif view == "done":
        stmt = stmt.where(Todo.done.is_(True))
    elif view == "today":
        stmt = stmt.where(Todo.due_date == current)
    elif view == "week":
        start, end = week_bounds(current)
        stmt = stmt.where(Todo.due_date >= start, Todo.due_date <= end)

    if tag_id is not None:
        stmt = stmt.where(Todo.tags.any(Tag.id == tag_id))

    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(or_(Todo.title.ilike(pattern), Todo.description.ilike(pattern)))

    stmt = stmt.order_by(
        Todo.done.asc(),
        Todo.system_key.is_(None).asc(),
        Todo.sort_order.asc(),
        Todo.due_date.asc().nullslast(),
        Todo.id.desc(),
    )
    result = await session.execute(stmt.limit(limit))
    return list(result.scalars().unique().all())


async def get_todo(session: AsyncSession, todo_id: int) -> Todo:
    # todo_out 会读取 tags；异步会话里必须在这里预加载，否则序列化时触发 MissingGreenlet
    todo = await session.get(Todo, todo_id, options=(selectinload(Todo.tags),))
    if todo is None or todo.deleted_at is not None:
        raise NotFoundError("待办不存在")
    return todo


async def _resolve_tags(session: AsyncSession, tag_ids: list[int] | None) -> list[Tag]:
    if not tag_ids:
        return []
    result = await session.execute(
        select(Tag).where(Tag.id.in_(tag_ids), Tag.deleted_at.is_(None))
    )
    tags = list(result.scalars().all())
    if len(tags) != len(set(tag_ids)):
        raise ValidationError("包含不存在的标签")
    return tags


def _rule_of(todo: Todo) -> RecurrenceRule:
    weekdays = tuple(int(x) for x in todo.weekdays.split(",")) if todo.weekdays else ()
    return RecurrenceRule(
        frequency=todo.frequency or "none",
        interval=todo.interval or 1,
        weekdays=weekdays,
        until=todo.until,
    )


async def create_todo(
    session: AsyncSession,
    *,
    title: str,
    description: str | None = None,
    due_date: date | None = None,
    frequency: str = "none",
    interval: int = 1,
    weekdays: list[int] | None = None,
    until: date | None = None,
    tag_ids: list[int] | None = None,
    system_key: str | None = None,
) -> Todo:
    if not title.strip():
        raise ValidationError("标题不能为空")
    if interval < 1:
        raise ValidationError("循环间隔必须大于 0")

    # 提前构造一次以校验规则合法性
    RecurrenceRule(frequency=frequency, interval=interval, weekdays=tuple(weekdays or ()), until=until)

    todo = Todo(
        title=title.strip(),
        description=description,
        due_date=due_date,
        frequency=frequency,
        interval=interval,
        weekdays=",".join(str(x) for x in weekdays) if weekdays else None,
        until=until,
        system_key=system_key,
        tags=await _resolve_tags(session, tag_ids),
    )
    session.add(todo)
    await session.flush()
    return todo


async def update_todo(session: AsyncSession, todo: Todo, **fields) -> Todo:
    tag_ids = fields.pop("tag_ids", None)
    weekdays = fields.pop("weekdays", None)

    for key, value in fields.items():
        if value is not None or key in {"description", "due_date", "until"}:
            setattr(todo, key, value)

    if weekdays is not None:
        todo.weekdays = ",".join(str(x) for x in weekdays) if weekdays else None

    if tag_ids is not None:
        todo.tags = await _resolve_tags(session, tag_ids)

    await session.flush()
    return todo


async def soft_delete(session: AsyncSession, todo: Todo) -> None:
    todo.deleted_at = datetime.now(timezone.utc)
    await session.flush()


async def toggle(session: AsyncSession, todo: Todo) -> tuple[Todo, Todo | None]:
    """切换完成状态；完成循环待办时生成下一实例。"""
    todo.done = not todo.done
    next_todo: Todo | None = None

    if todo.done:
        todo.completed_at = datetime.now(timezone.utc)
        rule = _rule_of(todo)
        base = todo.due_date or today()
        upcoming = next_occurrence(base, rule)
        if upcoming is not None:
            next_todo = Todo(
                title=todo.title,
                description=todo.description,
                due_date=upcoming,
                frequency=todo.frequency,
                interval=todo.interval,
                weekdays=todo.weekdays,
                until=todo.until,
                parent_id=todo.parent_id or todo.id,
                occurrence_index=(todo.occurrence_index or 0) + 1,
                sort_order=todo.sort_order,
                tags=list(todo.tags),
            )
            session.add(next_todo)
    else:
        todo.completed_at = None

    await session.flush()
    return todo, next_todo

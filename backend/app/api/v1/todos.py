"""待办接口。"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.core.deps import OwnerDep, SessionDep
from app.schemas.requests import TodoCreate, TodoUpdate
from app.schemas.serializers import todo_out
from app.services import todos as service
from app.services.clock import today
from app.services.daily import run_daily_maintenance

router = APIRouter(prefix="/todos", tags=["todos"], dependencies=[])


@router.get("")
async def list_todos(
    session: SessionDep,
    owner: OwnerDep,
    view: Annotated[str, Query(pattern="^(all|pending|today|week|done)$")] = "all",
    tag_id: int | None = None,
    q: str | None = None,
    limit: int = 200,
) -> dict:
    # 懒创建兜底：即使定时任务错过，打开待办页也能补齐当天三条系统待办
    await run_daily_maintenance(session, today())
    items = await service.list_todos(session, view=view, tag_id=tag_id, q=q, limit=limit)
    return {"items": [todo_out(t) for t in items], "count": len(items)}


@router.post("", status_code=201)
async def create_todo(payload: TodoCreate, session: SessionDep, owner: OwnerDep) -> dict:
    todo = await service.create_todo(session, **payload.model_dump())
    return todo_out(todo)


@router.patch("/{todo_id}")
async def update_todo(
    todo_id: int, payload: TodoUpdate, session: SessionDep, owner: OwnerDep
) -> dict:
    todo = await service.get_todo(session, todo_id)
    updated = await service.update_todo(session, todo, **payload.model_dump(exclude_unset=True))
    return todo_out(updated)


@router.post("/{todo_id}/toggle")
async def toggle_todo(todo_id: int, session: SessionDep, owner: OwnerDep) -> dict:
    todo = await service.get_todo(session, todo_id)
    updated, next_todo = await service.toggle(session, todo)
    return {
        "todo": todo_out(updated),
        "next": todo_out(next_todo) if next_todo else None,
    }


@router.delete("/{todo_id}")
async def delete_todo(todo_id: int, session: SessionDep, owner: OwnerDep) -> dict:
    todo = await service.get_todo(session, todo_id)
    await service.soft_delete(session, todo)
    return {"ok": True}

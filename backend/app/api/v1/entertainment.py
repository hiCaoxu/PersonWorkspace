"""娱乐看板接口：五类内容与三态切换。"""

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import or_, select

from app.core.deps import OwnerDep, SessionDep
from app.core.errors import NotFoundError
from app.models.entertainment import Entertainment
from app.schemas.requests import EntertainmentCreate, EntertainmentUpdate
from app.schemas.serializers import entertainment_out

router = APIRouter(prefix="/entertainment", tags=["entertainment"])


@router.get("")
async def list_items(
    session: SessionDep,
    owner: OwnerDep,
    ent_type: str | None = None,
    status: str | None = None,
    q: str = "",
) -> dict:
    stmt = select(Entertainment).where(Entertainment.deleted_at.is_(None))
    if ent_type:
        stmt = stmt.where(Entertainment.ent_type == ent_type)
    if status:
        stmt = stmt.where(Entertainment.status == status)
    if q.strip():
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(Entertainment.title.ilike(pattern), Entertainment.review.ilike(pattern))
        )

    stmt = stmt.order_by(
        Entertainment.is_pinned.desc(),
        Entertainment.sort_order.asc(),
        Entertainment.updated_at.desc(),
    )
    items = list((await session.execute(stmt)).scalars().all())
    return {"items": [entertainment_out(i) for i in items], "count": len(items)}


@router.post("", status_code=201)
async def create_item(
    payload: EntertainmentCreate, session: SessionDep, owner: OwnerDep
) -> dict:
    item = Entertainment(**payload.model_dump())
    session.add(item)
    await session.flush()
    return entertainment_out(item)


@router.patch("/{item_id}")
async def update_item(
    item_id: int, payload: EntertainmentUpdate, session: SessionDep, owner: OwnerDep
) -> dict:
    item = await session.get(Entertainment, item_id)
    if item is None or item.deleted_at is not None:
        raise NotFoundError("条目不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await session.flush()
    return entertainment_out(item)


@router.patch("/{item_id}/status")
async def move_status(
    item_id: int, status: str, session: SessionDep, owner: OwnerDep
) -> dict:
    if status not in {"want", "doing", "done"}:
        raise NotFoundError("状态不合法")
    item = await session.get(Entertainment, item_id)
    if item is None or item.deleted_at is not None:
        raise NotFoundError("条目不存在")

    item.status = status
    if status == "done":
        item.progress = 100
    await session.flush()
    return entertainment_out(item)


@router.delete("/{item_id}")
async def delete_item(item_id: int, session: SessionDep, owner: OwnerDep) -> dict:
    item = await session.get(Entertainment, item_id)
    if item is None or item.deleted_at is not None:
        raise NotFoundError("条目不存在")
    item.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return {"ok": True}

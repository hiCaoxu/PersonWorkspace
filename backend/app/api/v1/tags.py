"""标签接口。"""

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.deps import OwnerDep, SessionDep
from app.core.errors import ConflictError, NotFoundError
from app.models.tag import Tag
from app.schemas.requests import TagCreate
from app.schemas.serializers import tag_out

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("")
async def list_tags(
    session: SessionDep,
    owner: OwnerDep,
    scope: Annotated[str | None, Query(pattern="^(todo|note)$")] = None,
) -> dict:
    stmt = select(Tag).where(Tag.deleted_at.is_(None))
    if scope:
        stmt = stmt.where(Tag.scope == scope)
    stmt = stmt.order_by(Tag.scope, Tag.id)
    items = list((await session.execute(stmt)).scalars().all())
    return {"items": [tag_out(t) for t in items]}


@router.post("", status_code=201)
async def create_tag(payload: TagCreate, session: SessionDep, owner: OwnerDep) -> dict:
    exists = await session.scalar(
        select(Tag).where(
            Tag.name == payload.name, Tag.scope == payload.scope, Tag.deleted_at.is_(None)
        )
    )
    if exists:
        return tag_out(exists)

    tag = Tag(name=payload.name.strip(), scope=payload.scope, color=payload.color)
    session.add(tag)
    try:
        await session.flush()
    except Exception as exc:  # noqa: BLE001
        raise ConflictError("同名标签已存在") from exc
    return tag_out(tag)


@router.delete("/{tag_id}")
async def delete_tag(tag_id: int, session: SessionDep, owner: OwnerDep) -> dict:
    tag = await session.get(Tag, tag_id)
    if tag is None or tag.deleted_at is not None:
        raise NotFoundError("标签不存在")
    from datetime import datetime, timezone

    tag.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return {"ok": True}

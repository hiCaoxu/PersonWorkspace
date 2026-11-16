"""笔记接口：搜索、标签筛选与 CRUD。"""

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import OwnerDep, SessionDep
from app.core.errors import NotFoundError, ValidationError
from app.models.note import Note
from app.models.tag import Tag
from app.schemas.requests import NoteCreate, NoteUpdate
from app.schemas.serializers import note_out
from app.services.notes import search_notes, soft_delete_note

router = APIRouter(prefix="/notes", tags=["notes"])


async def _resolve_tags(session, tag_ids: list[int]) -> list[Tag]:
    if not tag_ids:
        return []
    result = await session.execute(
        select(Tag).where(Tag.id.in_(tag_ids), Tag.deleted_at.is_(None))
    )
    tags = list(result.scalars().all())
    if len(tags) != len(set(tag_ids)):
        raise ValidationError("包含不存在的标签")
    return tags


@router.get("")
async def list_notes(
    session: SessionDep,
    owner: OwnerDep,
    q: str = "",
    tag_id: int | None = None,
    limit: int = 50,
) -> dict:
    items = await search_notes(session, q=q, tag_id=tag_id, limit=limit)
    return {"items": [note_out(n, with_content=False) for n in items], "count": len(items)}


@router.get("/random")
async def random_note(session: SessionDep, owner: OwnerDep) -> dict:
    from app.services.dashboard import random_note as pick

    note = await pick(session)
    return {"note": note_out(note) if note else None}


@router.get("/{note_id}")
async def get_note(note_id: int, session: SessionDep, owner: OwnerDep) -> dict:
    stmt = select(Note).options(selectinload(Note.tags)).where(Note.id == note_id)
    note = (await session.execute(stmt)).scalars().unique().first()
    if note is None or note.deleted_at is not None:
        raise NotFoundError("笔记不存在")
    return note_out(note)


@router.post("", status_code=201)
async def create_note(payload: NoteCreate, session: SessionDep, owner: OwnerDep) -> dict:
    note = Note(
        title=payload.title.strip() or "无标题",
        content_md=payload.content_md,
        tags=await _resolve_tags(session, payload.tag_ids),
    )
    session.add(note)
    await session.flush()
    return note_out(note)


@router.patch("/{note_id}")
async def update_note(
    note_id: int, payload: NoteUpdate, session: SessionDep, owner: OwnerDep
) -> dict:
    stmt = select(Note).options(selectinload(Note.tags)).where(Note.id == note_id)
    note = (await session.execute(stmt)).scalars().unique().first()
    if note is None or note.deleted_at is not None:
        raise NotFoundError("笔记不存在")

    data = payload.model_dump(exclude_unset=True)
    tag_ids = data.pop("tag_ids", None)
    for key, value in data.items():
        setattr(note, key, value)
    if tag_ids is not None:
        note.tags = await _resolve_tags(session, tag_ids)

    await session.flush()
    return note_out(note)


@router.delete("/{note_id}")
async def delete_note(note_id: int, session: SessionDep, owner: OwnerDep) -> dict:
    stmt = select(Note).where(Note.id == note_id)
    note = (await session.execute(stmt)).scalars().first()
    if note is None or note.deleted_at is not None:
        raise NotFoundError("笔记不存在")
    await soft_delete_note(session, note)
    return {"ok": True}

"""笔记：搜索与标签筛选。"""

from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note, note_tag


async def search_notes(
    session: AsyncSession,
    q: str = "",
    tag_id: int | None = None,
    limit: int = 50,
) -> list[Note]:
    limit = max(1, min(limit, 200))
    stmt = select(Note).where(Note.deleted_at.is_(None))

    keyword = (q or "").strip()
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(or_(Note.title.ilike(pattern), Note.content_md.ilike(pattern)))

    if tag_id is not None:
        stmt = stmt.where(
            Note.id.in_(select(note_tag.c.note_id).where(note_tag.c.tag_id == tag_id))
        )

    stmt = stmt.order_by(Note.is_pinned.desc(), Note.updated_at.desc(), Note.id.desc())
    result = await session.execute(stmt.limit(limit))
    return list(result.scalars().unique().all())


async def soft_delete_note(session: AsyncSession, note: Note) -> None:
    note.deleted_at = datetime.now(timezone.utc)
    await session.flush()

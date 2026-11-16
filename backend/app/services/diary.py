"""日记：每日唯一一篇，懒创建兜底（配合 00:05 定时任务双保险）。"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diary import Diary
from app.services.diary_title import format_diary_title


async def ensure_diary(session: AsyncSession, day: date) -> Diary:
    """存在即返回，不存在则按 ISO 周标题创建；重复调用不产生第二篇。"""
    stmt = (
        pg_insert(Diary)
        .values(diary_date=day, title=format_diary_title(day), content="")
        .on_conflict_do_nothing(index_elements=["diary_date"])
    )
    await session.execute(stmt)
    await session.flush()

    result = await session.execute(select(Diary).where(Diary.diary_date == day))
    return result.scalar_one()


async def get_diary(session: AsyncSession, day: date) -> Diary | None:
    result = await session.execute(
        select(Diary).where(Diary.diary_date == day, Diary.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()

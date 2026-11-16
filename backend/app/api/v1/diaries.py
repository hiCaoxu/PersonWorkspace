"""日记接口：每天唯一一篇，打开即创建。"""

import calendar
from datetime import date

from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import OwnerDep, SessionDep
from app.core.errors import NotFoundError
from app.models.diary import Diary
from app.schemas.requests import DiaryUpdate
from app.schemas.serializers import diary_out
from app.services.clock import today
from app.services.diary import ensure_diary
from app.services.lunar import lunar_text

router = APIRouter(prefix="/diaries", tags=["diaries"])


def _detail(diary: Diary) -> dict:
    data = diary_out(diary)
    data["lunar"] = lunar_text(diary.diary_date, with_year=False)
    return data


@router.get("/today")
async def diary_today(session: SessionDep, owner: OwnerDep) -> dict:
    diary = await ensure_diary(session, today())
    return _detail(diary)


@router.get("/by-date/{day}")
async def diary_by_date(day: date, session: SessionDep, owner: OwnerDep) -> dict:
    diary = await ensure_diary(session, day)
    return _detail(diary)


@router.get("")
async def list_diaries(
    session: SessionDep, year: int, month: int, owner: OwnerDep
) -> dict:
    if not 1 <= month <= 12:
        raise NotFoundError("月份不合法")
    last = calendar.monthrange(year, month)[1]
    stmt = (
        select(Diary)
        .where(
            Diary.deleted_at.is_(None),
            Diary.diary_date >= date(year, month, 1),
            Diary.diary_date <= date(year, month, last),
        )
        .order_by(Diary.diary_date.desc())
    )
    items = list((await session.execute(stmt)).scalars().all())
    return {
        "items": [{"id": d.id, "diary_date": d.diary_date.isoformat()} for d in items],
        "year": year,
        "month": month,
    }


@router.patch("/{diary_id}")
async def update_diary(
    diary_id: int, payload: DiaryUpdate, session: SessionDep, owner: OwnerDep
) -> dict:
    diary = await session.get(Diary, diary_id)
    if diary is None or diary.deleted_at is not None:
        raise NotFoundError("日记不存在")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(diary, key, value)
    await session.flush()
    return _detail(diary)

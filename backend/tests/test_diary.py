"""日记：每日一篇、标题格式、幂等创建。"""

from datetime import date

from sqlalchemy import func, select

from app.models.diary import Diary
from app.services.diary import ensure_diary, get_diary

DAY = date(2026, 11, 15)


async def test_creates_diary_with_iso_week_title(db):
    diary = await ensure_diary(db, DAY)
    assert diary.title == "2026年11月15日 46周星期日"
    assert diary.diary_date == DAY
    assert diary.content == ""


async def test_ensure_is_idempotent(db):
    first = await ensure_diary(db, DAY)
    second = await ensure_diary(db, DAY)
    assert first.id == second.id

    count = (
        await db.execute(select(func.count()).select_from(Diary).where(Diary.diary_date == DAY))
    ).scalar_one()
    assert count == 1


async def test_does_not_overwrite_existing_content(db):
    diary = await ensure_diary(db, DAY)
    diary.content = "今天读完了一本书。"
    await db.flush()

    again = await ensure_diary(db, DAY)
    assert again.content == "今天读完了一本书。"


async def test_each_day_gets_its_own_diary(db):
    await ensure_diary(db, DAY)
    await ensure_diary(db, date(2026, 11, 16))
    total = (await db.execute(select(func.count()).select_from(Diary))).scalar_one()
    assert total == 2


async def test_get_diary_returns_none_when_missing(db):
    assert await get_diary(db, DAY) is None


async def test_get_diary_returns_created(db):
    created = await ensure_diary(db, DAY)
    found = await get_diary(db, DAY)
    assert found is not None
    assert found.id == created.id


async def test_title_cross_year(db):
    diary = await ensure_diary(db, date(2027, 1, 1))
    assert diary.title == "2027年1月1日 53周星期五"

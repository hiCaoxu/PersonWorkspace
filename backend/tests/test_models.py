"""数据模型约束：唯一索引、软删除字段、标签关联。"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.diary import Diary
from app.models.food import FoodItem
from app.models.note import Note
from app.models.tag import Tag
from app.models.todo import Todo


async def _expect_integrity_error(db, statement) -> None:
    try:
        async with db.begin_nested():
            await db.execute(statement)
            await db.flush()
    except IntegrityError:
        return
    raise AssertionError("期望触发唯一约束，但没有触发")


async def test_diary_date_is_unique(db):
    db.add(Diary(diary_date=date(2026, 11, 15), title="2026年11月15日 46周星期日"))
    await db.flush()
    await _expect_integrity_error(
        db,
        Diary.__table__.insert().values(
            diary_date=date(2026, 11, 15), title="重复日期", content=""
        ),
    )


async def test_food_name_is_unique(db):
    db.add(FoodItem(name="米饭", energy_kcal_per_100g=116))
    await db.flush()
    await _expect_integrity_error(
        db,
        FoodItem.__table__.insert().values(name="米饭", energy_kcal_per_100g=200),
    )


async def test_tag_unique_per_scope(db):
    db.add(Tag(name="工作", scope="todo"))
    await db.flush()
    await _expect_integrity_error(
        db, Tag.__table__.insert().values(name="工作", scope="todo", color="#000000")
    )
    # 不同作用域允许同名
    db.add(Tag(name="工作", scope="note"))
    await db.flush()


async def test_system_todo_partial_unique_index(db):
    db.add(Todo(title="记账", due_date=date(2026, 11, 15), system_key="finance"))
    await db.flush()
    await _expect_integrity_error(
        db,
        Todo.__table__.insert().values(
            title="重复", due_date=date(2026, 11, 15), system_key="finance", done=False,
            frequency="none", interval=1, sort_order=0,
        ),
    )


async def test_normal_todos_are_not_limited_by_system_index(db):
    db.add_all(
        [
            Todo(title="买牛奶", due_date=date(2026, 11, 15)),
            Todo(title="交电费", due_date=date(2026, 11, 15)),
        ]
    )
    await db.flush()
    rows = (await db.execute(select(Todo).where(Todo.due_date == date(2026, 11, 15)))).scalars().all()
    assert len(rows) == 2


async def test_todo_tag_relationship(db):
    tag = Tag(name="生活", scope="todo")
    todo = Todo(title="整理房间", due_date=date(2026, 11, 15), tags=[tag])
    db.add(todo)
    await db.flush()

    loaded = (await db.execute(select(Todo).where(Todo.id == todo.id))).scalar_one()
    assert [t.name for t in loaded.tags] == ["生活"]


async def test_note_tag_relationship(db):
    tag = Tag(name="灵感", scope="note")
    note = Note(title="周末计划", content_md="# 计划", tags=[tag])
    db.add(note)
    await db.flush()

    loaded = (await db.execute(select(Note).where(Note.id == note.id))).scalar_one()
    assert [t.name for t in loaded.tags] == ["灵感"]


async def test_soft_delete_columns_exist(db):
    todo = Todo(title="可删除", due_date=date(2026, 11, 15))
    db.add(todo)
    await db.flush()
    assert todo.deleted_at is None
    assert todo.created_at is not None
    assert todo.updated_at is not None


async def test_pg_trgm_extension_available(db):
    from sqlalchemy import text

    result = await db.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'"))
    assert result.scalar_one() == 1


async def test_chinese_substring_match_uses_ilike_not_trgm(db):
    """中文匹配必须走 ILIKE：C locale 下 pg_trgm 对汉字不产生 trigram。"""
    from sqlalchemy import text

    trgm = await db.execute(text("SELECT similarity('米饭', '米饭')"))
    assert float(trgm.scalar_one()) == 0.0

    ilike = await db.execute(text("SELECT '米饭' ILIKE '%米饭%'"))
    assert ilike.scalar_one() is True

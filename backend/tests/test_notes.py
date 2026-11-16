"""笔记：标题/正文搜索、标签筛选、软删除隔离。"""

import pytest_asyncio

from app.models.note import Note
from app.models.tag import Tag
from app.services.notes import search_notes, soft_delete_note


@pytest_asyncio.fixture
async def notes(db):
    tag_tech = Tag(name="技术", scope="note")
    tag_life = Tag(name="生活", scope="note")
    db.add_all([tag_tech, tag_life])
    await db.flush()

    db.add_all(
        [
            Note(
                title="FastAPI 分页实践",
                content_md="# 分页\n\n使用 limit 与 offset 控制单页数量。",
                tags=[tag_tech],
            ),
            Note(
                title="周末骑行路线",
                content_md="从五河县城沿浍河向北，全程约 32 公里。",
                tags=[tag_life],
            ),
            Note(
                title="数据库索引笔记",
                content_md="复合索引遵循最左前缀原则。",
                tags=[tag_tech],
            ),
        ]
    )
    await db.flush()
    return {"tech": tag_tech, "life": tag_life}


async def test_search_by_title(db, notes):
    results = await search_notes(db, "骑行")
    assert [n.title for n in results] == ["周末骑行路线"]


async def test_search_by_content(db, notes):
    results = await search_notes(db, "最左前缀")
    assert [n.title for n in results] == ["数据库索引笔记"]


async def test_search_returns_empty_for_unknown(db, notes):
    assert await search_notes(db, "不存在的关键词") == []


async def test_filter_by_tag(db, notes):
    results = await search_notes(db, tag_id=notes["tech"].id)
    assert {n.title for n in results} == {"FastAPI 分页实践", "数据库索引笔记"}


async def test_tag_filter_combined_with_keyword(db, notes):
    results = await search_notes(db, "索引", tag_id=notes["tech"].id)
    assert [n.title for n in results] == ["数据库索引笔记"]


async def test_soft_deleted_note_hidden(db, notes):
    results = await search_notes(db, "骑行")
    await soft_delete_note(db, results[0])
    assert await search_notes(db, "骑行") == []


async def test_limit_is_clamped(db, notes):
    assert len(await search_notes(db, limit=9999)) == 3


async def test_results_ordered_by_updated_at(db, notes):
    results = await search_notes(db)
    assert len(results) == 3
    timestamps = [n.updated_at for n in results]
    assert timestamps == sorted(timestamps, reverse=True)

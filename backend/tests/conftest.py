"""测试夹具：真实 PostgreSQL（含 pg_trgm），每个用例事务回滚保证隔离。

不使用 session 级 async fixture，避免 pytest-asyncio 的跨 loop 绑定问题：
建表在一次性的 asyncio.run 中完成，用例各自建立 NullPool 引擎。
"""

import asyncio
import os

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

import app.models  # noqa: F401  确保全部模型注册到 Base.metadata
from app.db.base import Base

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://pwtest:pwtest@127.0.0.1:55432/pwtest_test",
)


async def _prepare_schema() -> None:
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    asyncio.run(_prepare_schema())
    yield


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture
async def db(engine):
    """独立事务，用例结束后整体回滚。"""
    conn = await engine.connect()
    trans = await conn.begin()
    session = AsyncSession(bind=conn, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await conn.close()


@pytest.fixture
def secret_key() -> bytes:
    return b"0" * 32

"""每日维护任务：日记与三条系统待办（定时 + 懒创建双保险）。"""

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import AppSetting
from app.services.clock import today
from app.services.diary import ensure_diary
from app.services.system_todos import ensure_today_system_todos

logger = logging.getLogger("app.daily")

SETTING_KEY = "daily_system_todos_enabled"


async def _system_todos_enabled(session: AsyncSession) -> bool:
    row = await session.scalar(select(AppSetting).where(AppSetting.key == SETTING_KEY))
    if row is None:
        return True
    return str(row.value).strip().lower() in {"true", "1", "yes", "on"}


async def run_daily_maintenance(
    session: AsyncSession, day: date | None = None, *, force: bool = False
) -> dict:
    target = day or today()
    enabled = force or await _system_todos_enabled(session)

    diary = await ensure_diary(session, target)
    todos = await ensure_today_system_todos(session, target, enabled=enabled)

    logger.info(
        "每日维护完成 day=%s diary_id=%s system_todos=%d",
        target,
        diary.id,
        len(todos),
    )
    return {"day": target, "diary_id": diary.id, "system_todos": len(todos)}

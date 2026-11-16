"""定时任务：每日 00:05 生成日记与三条系统待办。

为避免多 worker 重复调度，容器默认单 worker（见 entrypoint.sh）。
即使重复执行，写入侧也有唯一约束 + ON CONFLICT 兜底。
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings

logger = logging.getLogger("app.scheduler")

_scheduler: AsyncIOScheduler | None = None


async def _daily_job() -> None:
    from app.db.session import SessionLocal
    from app.services.daily import run_daily_maintenance

    try:
        async with SessionLocal() as session:
            async with session.begin():
                await run_daily_maintenance(session)
    except Exception:  # noqa: BLE001
        logger.exception("每日维护任务失败")


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.add_job(
        _daily_job,
        CronTrigger(hour=0, minute=5),
        id="daily-maintenance",
        replace_existing=True,
        misfire_grace_time=3600,
        coalesce=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("定时任务已启动 timezone=%s 每日 00:05", settings.timezone)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("定时任务已停止")

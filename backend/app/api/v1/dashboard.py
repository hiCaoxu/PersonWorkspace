"""首页聚合接口。"""

from fastapi import APIRouter

from app.core.deps import OwnerDep, SessionDep
from app.schemas.serializers import money, note_out, todo_out
from app.services.clock import today, week_bounds
from app.services.daily import run_daily_maintenance
from app.services.dashboard import build_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def summary(session: SessionDep, owner: OwnerDep) -> dict:
    current = today()
    # 懒创建：确保今天的日记与三条系统待办存在
    await run_daily_maintenance(session, current)

    data = await build_dashboard(session, current)
    week_start, week_end = week_bounds(current)

    return {
        "date": current.isoformat(),
        "lunar": data["lunar"],
        "zodiac": data["zodiac"],
        "week_range": {"start": week_start.isoformat(), "end": week_end.isoformat()},
        "month_income": money(data["month_income"]),
        "month_expense": money(data["month_expense"]),
        "total_assets": money(data["total_assets"]),
        "today_todos": [todo_out(t) for t in data["today_todos"]],
        "week_todos": [todo_out(t) for t in data["week_todos"]],
        "random_note": note_out(data["random_note"]) if data["random_note"] else None,
    }

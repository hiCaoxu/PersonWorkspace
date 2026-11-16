"""增量同步：返回指定时间点之后发生变更的实体摘要，供多端失效缓存。"""

from datetime import datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import or_, select

from app.core.deps import OwnerDep, SessionDep
from app.models.diary import Diary
from app.models.entertainment import Entertainment
from app.models.finance import Account, Transaction
from app.models.health import HealthDiet, HealthExercise, HealthSleep, HealthWeight
from app.models.note import Note
from app.models.profile import LifeEvent
from app.models.todo import Todo
from app.services.clock import now

router = APIRouter(prefix="/sync", tags=["sync"])

SYNC_MODELS: dict[str, type] = {
    "todos": Todo,
    "notes": Note,
    "diaries": Diary,
    "exercises": HealthExercise,
    "diets": HealthDiet,
    "weights": HealthWeight,
    "sleeps": HealthSleep,
    "entertainment": Entertainment,
    "accounts": Account,
    "transactions": Transaction,
    "life_events": LifeEvent,
}


@router.get("/changes")
async def changes(session: SessionDep, owner: OwnerDep, since: datetime | None = None) -> dict:
    cursor = since or (now() - timedelta(days=1))

    payload: dict[str, list[dict]] = {}
    for name, model in SYNC_MODELS.items():
        stmt = (
            select(model.id, model.updated_at, model.deleted_at)
            .where(
                or_(model.updated_at > cursor, model.deleted_at > cursor)
            )
            .limit(500)
        )
        rows = (await session.execute(stmt)).all()
        payload[name] = [
            {
                "id": row[0],
                "updated_at": row[1].isoformat() if row[1] else None,
                "deleted": row[2] is not None,
            }
            for row in rows
        ]

    return {"server_time": now().isoformat(), "since": cursor.isoformat(), "changes": payload}

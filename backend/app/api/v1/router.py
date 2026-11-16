"""API v1 路由汇总。"""

from fastapi import APIRouter, Depends

from app.api.v1 import (
    auth,
    dashboard,
    diaries,
    entertainment,
    finance,
    foods,
    health,
    meta,
    notes,
    profile,
    sync,
    tags,
    todos,
    upload,
)
from app.core.deps import require_xhr

api_router = APIRouter(dependencies=[Depends(require_xhr)])

api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(todos.router)
api_router.include_router(tags.router)
api_router.include_router(diaries.router)
api_router.include_router(notes.router)
api_router.include_router(foods.router)
api_router.include_router(meta.router)
api_router.include_router(health.router)
api_router.include_router(finance.router)
api_router.include_router(entertainment.router)
api_router.include_router(profile.router)
api_router.include_router(upload.router)
api_router.include_router(sync.router)

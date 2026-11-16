"""应用装配：中间件、异常处理、路由与启动钩子。"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import RequestContextMiddleware, configure_logging

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging("DEBUG" if settings.debug else "INFO")
    logger.info("应用启动 name=%s", settings.app_name)
    try:
        from app.services.scheduler import start_scheduler, stop_scheduler

        start_scheduler()
    except Exception:  # noqa: BLE001
        logger.exception("定时任务启动失败")
    yield
    try:
        from app.services.scheduler import stop_scheduler

        stop_scheduler()
    except Exception:  # noqa: BLE001
        logger.exception("定时任务停止失败")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="个人工作台 API",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    register_exception_handlers(app)

    from app.api.v1.router import api_router

    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/health", tags=["system"])
    async def health() -> dict:
        return {"status": "ok", "app": settings.app_name, "version": "0.1.0"}

    return app


app = create_app()

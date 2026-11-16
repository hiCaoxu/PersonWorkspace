"""统一错误类型与 JSON 错误响应。"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.error")


class AppError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str = "请求有误", *, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"

    def __init__(self, message: str = "资源不存在"):
        super().__init__(message)


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"

    def __init__(self, message: str = "请先登录"):
        super().__init__(message)


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"

    def __init__(self, message: str = "无权执行该操作"):
        super().__init__(message)


class ConflictError(AppError):
    status_code = 409
    code = "conflict"

    def __init__(self, message: str = "数据冲突"):
        super().__init__(message)


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"

    def __init__(self, message: str = "参数校验失败"):
        super().__init__(message)


def _payload(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_payload(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(p) for p in first.get("loc", []) if p != "body")
        message = f"{loc}: {first.get('msg', '参数不合法')}" if loc else "参数不合法"
        return JSONResponse(status_code=422, content=_payload("validation_error", message))

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(f"http_{exc.status_code}", str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("未捕获异常 path=%s", request.url.path)
        return JSONResponse(status_code=500, content=_payload("internal_error", "服务端异常"))

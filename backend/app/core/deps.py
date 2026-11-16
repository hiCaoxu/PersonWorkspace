"""依赖注入：会话、鉴权、CSRF 头校验、分页。"""

from typing import Annotated

from fastapi import Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import SCOPE_SESSION, AuthError, decode_token
from app.db.session import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


async def current_owner(request: Request) -> str:
    token = request.cookies.get(settings.session_cookie)
    if not token:
        raise UnauthorizedError("请先登录")
    try:
        payload = decode_token(token, settings.secret_key, expected_scope=SCOPE_SESSION)
    except AuthError as exc:
        raise UnauthorizedError(str(exc)) from exc
    return str(payload.get("sub", "owner"))


OwnerDep = Annotated[str, Depends(current_owner)]


async def require_xhr(request: Request) -> None:
    """写操作强制自定义头，配合 SameSite=Lax 抵御 CSRF。"""
    if request.method in WRITE_METHODS:
        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            raise ForbiddenError("缺少必要的请求头")


class Pagination:
    def __init__(
        self,
        limit: Annotated[int, Query(ge=1, le=200)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> None:
        self.limit = limit
        self.offset = offset


PaginationDep = Annotated[Pagination, Depends(Pagination)]

"""认证：单口令登录、登出、改口令与身份证二次验证。"""

import time
from collections import defaultdict, deque

from fastapi import APIRouter, Request, Response
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import OwnerDep, SessionDep
from app.core.errors import UnauthorizedError, ValidationError
from app.core.security import (
    create_reveal_ticket,
    create_token,
    hash_passcode,
    verify_passcode,
)
from app.models.auth import AuthCredential
from app.schemas.auth import (
    ChangePasscodeRequest,
    LoginRequest,
    MeResponse,
    RevealRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_failures: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Real-IP")
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"


def _guard(ip: str) -> None:
    window = settings.login_window_minutes * 60
    bucket = _failures[ip]
    cutoff = time.time() - window
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= settings.login_max_attempts:
        raise UnauthorizedError(
            f"尝试过于频繁，请 {settings.login_window_minutes} 分钟后再试"
        )


def _record_failure(ip: str) -> None:
    _failures[ip].append(time.time())


async def _first_credential(session) -> AuthCredential:
    credential = await session.scalar(select(AuthCredential).order_by(AuthCredential.id).limit(1))
    if credential is None:
        raise ValidationError("尚未初始化登录口令")
    return credential


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: SessionDep,
) -> dict:
    ip = _client_ip(request)
    _guard(ip)

    credential = await _first_credential(session)
    if not verify_passcode(payload.passcode, credential.passcode_hash):
        _record_failure(ip)
        raise UnauthorizedError("口令不正确")

    _failures.pop(ip, None)
    token = create_token(settings.secret_key, ttl_minutes=settings.token_ttl_minutes)
    response.set_cookie(
        key=settings.session_cookie,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.token_ttl_minutes * 60,
        path="/",
    )
    return {"ok": True}


@router.post("/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie(settings.session_cookie, path="/")
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def me(owner: OwnerDep) -> MeResponse:
    return MeResponse(owner=owner, app_name=settings.app_name)


@router.post("/change-passcode")
async def change_passcode(
    payload: ChangePasscodeRequest,
    session: SessionDep,
    owner: OwnerDep,
) -> dict:
    credential = await _first_credential(session)
    if not verify_passcode(payload.old_passcode, credential.passcode_hash):
        raise UnauthorizedError("原口令不正确")
    if payload.old_passcode == payload.new_passcode:
        raise ValidationError("新口令不能与原口令相同")

    credential.passcode_hash = hash_passcode(payload.new_passcode)
    await session.flush()
    return {"ok": True}


@router.post("/reveal")
async def reveal(payload: RevealRequest, session: SessionDep, owner: OwnerDep) -> dict:
    credential = await _first_credential(session)
    if not verify_passcode(payload.passcode, credential.passcode_hash):
        raise UnauthorizedError("口令不正确")

    ticket = create_reveal_ticket(
        settings.secret_key, ttl_minutes=settings.reveal_ttl_minutes
    )
    return {"ticket": ticket, "expires_in": settings.reveal_ttl_minutes * 60}

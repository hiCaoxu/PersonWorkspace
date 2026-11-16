"""口令哈希、JWT 签发与二次验证票据。"""

from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()
ALGORITHM = "HS256"

SCOPE_SESSION = "session"
SCOPE_REVEAL = "reveal"


class AuthError(ValueError):
    pass


def hash_passcode(passcode: str) -> str:
    if len(passcode) < 6:
        raise AuthError("口令至少 6 位")
    return _hasher.hash(passcode)


def verify_passcode(passcode: str, stored_hash: str) -> bool:
    try:
        return _hasher.verify(stored_hash, passcode)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(stored_hash)
    except InvalidHashError:
        return False


def _issue(secret: str, subject: str, scope: str, ttl_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "scope": scope,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def create_token(secret: str, subject: str = "owner", ttl_minutes: int = 60 * 24 * 7) -> str:
    return _issue(secret, subject, SCOPE_SESSION, ttl_minutes)


def create_reveal_ticket(secret: str, subject: str = "owner", ttl_minutes: int = 5) -> str:
    return _issue(secret, subject, SCOPE_REVEAL, ttl_minutes)


def decode_token(token: str, secret: str, *, expected_scope: str = SCOPE_SESSION) -> dict:
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("登录已过期，请重新登录") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("令牌无效") from exc

    if payload.get("scope") != expected_scope:
        raise AuthError("令牌用途不匹配")
    return payload

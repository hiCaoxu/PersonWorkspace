"""认证原语：argon2 口令与 JWT。"""

import pytest

from app.core.security import (
    AuthError,
    create_token,
    decode_token,
    hash_passcode,
    verify_passcode,
)

PASSCODE = "my-secret-passcode"


def test_hash_and_verify():
    hashed = hash_passcode(PASSCODE)
    assert hashed != PASSCODE
    assert verify_passcode(PASSCODE, hashed) is True
    assert verify_passcode("wrong-passcode", hashed) is False


def test_hash_is_salted():
    assert hash_passcode(PASSCODE) != hash_passcode(PASSCODE)


def test_short_passcode_rejected():
    with pytest.raises(AuthError):
        hash_passcode("12345")


def test_verify_against_garbage_hash_returns_false():
    assert verify_passcode(PASSCODE, "not-a-hash") is False


def test_token_roundtrip(secret_key):
    secret = secret_key.decode()
    token = create_token(secret)
    payload = decode_token(token, secret)
    assert payload["sub"] == "owner"
    assert payload["exp"] > payload["iat"]


def test_expired_token_rejected(secret_key):
    secret = secret_key.decode()
    token = create_token(secret, ttl_minutes=-1)
    with pytest.raises(AuthError):
        decode_token(token, secret)


def test_token_signed_by_other_key_rejected(secret_key):
    token = create_token("other-secret")
    with pytest.raises(AuthError):
        decode_token(token, secret_key.decode())


def test_malformed_token_rejected(secret_key):
    with pytest.raises(AuthError):
        decode_token("abc.def.ghi", secret_key.decode())

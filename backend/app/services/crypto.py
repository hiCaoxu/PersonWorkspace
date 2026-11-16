"""身份证加解密与脱敏。

密文格式：base64( nonce(12) + ciphertext + tag )
"""

import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_LEN = 12


class CryptoError(ValueError):
    pass


def _key(raw: bytes) -> bytes:
    if len(raw) != 32:
        raise CryptoError("AES-256 需要 32 字节密钥")
    return raw


def encrypt_text(plaintext: str, key: bytes) -> str:
    aes = AESGCM(_key(key))
    nonce = os.urandom(NONCE_LEN)
    cipher = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + cipher).decode("ascii")


def decrypt_text(token: str, key: bytes) -> str:
    try:
        blob = base64.b64decode(token, validate=True)
    except Exception as exc:  # noqa: BLE001
        raise CryptoError("密文格式错误") from exc
    if len(blob) <= NONCE_LEN:
        raise CryptoError("密文长度异常")
    aes = AESGCM(_key(key))
    try:
        return aes.decrypt(blob[:NONCE_LEN], blob[NONCE_LEN:], None).decode("utf-8")
    except InvalidTag as exc:
        raise CryptoError("密文校验失败，可能已被篡改") from exc


def mask_id_card(id_card: str) -> str:
    """前 6 后 4，中间用 * 遮盖。"""
    cleaned = id_card.strip().upper()
    if len(cleaned) < 11:
        raise CryptoError("身份证号长度不足")
    return f"{cleaned[:6]}{'*' * (len(cleaned) - 10)}{cleaned[-4:]}"


def id_card_birthday(id_card: str) -> str:
    """从身份证号取出生日期（YYYY-MM-DD），仅作登记生日参考。"""
    cleaned = id_card.strip().upper()
    if len(cleaned) != 18:
        raise CryptoError("仅支持 18 位身份证号")
    birth = cleaned[6:14]
    return f"{birth[:4]}-{birth[4:6]}-{birth[6:8]}"

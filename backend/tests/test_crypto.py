"""身份证加解密与脱敏。"""

import base64

import pytest

from app.services.crypto import (
    CryptoError,
    decrypt_text,
    encrypt_text,
    id_card_birthday,
    mask_id_card,
)

ID_CARD = "340322199202057851"


def test_roundtrip(secret_key):
    token = encrypt_text(ID_CARD, secret_key)
    assert ID_CARD not in token
    assert decrypt_text(token, secret_key) == ID_CARD


def test_nonce_makes_output_unique(secret_key):
    assert encrypt_text(ID_CARD, secret_key) != encrypt_text(ID_CARD, secret_key)


def test_tampered_ciphertext_is_rejected(secret_key):
    blob = bytearray(base64.b64decode(encrypt_text("hello", secret_key)))
    blob[-1] ^= 0x01
    bad = base64.b64encode(bytes(blob)).decode()
    with pytest.raises(CryptoError):
        decrypt_text(bad, secret_key)


def test_wrong_key_is_rejected(secret_key):
    token = encrypt_text("hello", secret_key)
    with pytest.raises(CryptoError):
        decrypt_text(token, b"1" * 32)


def test_key_must_be_32_bytes(secret_key):
    with pytest.raises(CryptoError):
        encrypt_text("hello", b"short")


def test_mask_keeps_head_and_tail():
    assert mask_id_card(ID_CARD) == "340322********7851"
    assert len(mask_id_card(ID_CARD)) == len(ID_CARD)


def test_mask_rejects_short_input():
    with pytest.raises(CryptoError):
        mask_id_card("123")


def test_id_card_birthday_extracts_registration_date():
    # 证件登记生日为公历 1992-02-05，与真实农历生日不同
    assert id_card_birthday(ID_CARD) == "1992-02-05"


def test_id_card_birthday_requires_18_digits():
    with pytest.raises(CryptoError):
        id_card_birthday("340322920205785")

from __future__ import annotations

from datetime import timedelta

import jwt
import pytest

from interview_pilot.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing_verifies_plain_password() -> None:
    hashed = hash_password("strong-password")

    assert hashed != "strong-password"
    assert verify_password("strong-password", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_access_token_can_be_decoded_to_subject() -> None:
    token = create_access_token(subject="123")

    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert "exp" in payload


def test_expired_access_token_is_rejected() -> None:
    token = create_access_token(subject="123", expires_delta=timedelta(seconds=-1))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)

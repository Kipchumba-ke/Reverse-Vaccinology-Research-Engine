from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest

from app.models.user import User
from app.services.auth_service import _validate_registration
from app.services.token_service import create_token, decode_token


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only")
    monkeypatch.delenv("JWT_EXPIRES_MINUTES", raising=False)


def test_token_contains_expiry_in_the_future():
    token = create_token(User(email="a@example.com"))

    payload = jwt.decode(token, options={"verify_signature": False})

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    assert expires_at > datetime.now(timezone.utc) + timedelta(hours=23)


def test_token_lifetime_is_configurable(monkeypatch):
    monkeypatch.setenv("JWT_EXPIRES_MINUTES", "5")

    token = create_token(User(email="a@example.com"))
    payload = jwt.decode(token, options={"verify_signature": False})

    assert payload["exp"] - payload["iat"] == 5 * 60


@pytest.mark.parametrize("value", ["abc", "0", "-3"])
def test_invalid_token_lifetime_is_rejected(monkeypatch, value):
    monkeypatch.setenv("JWT_EXPIRES_MINUTES", value)

    with pytest.raises(RuntimeError):
        create_token(User(email="a@example.com"))


def test_valid_token_round_trips_user_id():
    user = User(email="a@example.com")

    assert decode_token(create_token(user)) == user.id


def test_expired_token_is_rejected():
    expired = jwt.encode(
        {
            "sub": str(uuid4()),
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        "test-secret-key-for-unit-tests-only",
        algorithm="HS256",
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired)


def test_token_without_expiry_is_rejected():
    no_expiry = jwt.encode(
        {"sub": str(uuid4())},
        "test-secret-key-for-unit-tests-only",
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(no_expiry)


def test_token_with_malformed_subject_is_an_invalid_token():
    bad_subject = jwt.encode(
        {
            "sub": "not-a-uuid",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        "test-secret-key-for-unit-tests-only",
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(bad_subject)


def test_valid_registration_input_is_accepted():
    _validate_registration("person@example.com", "password123")


@pytest.mark.parametrize(
    "email",
    ["", "no-at-sign", "a@b", "a b@example.com", None, 42, "x" * 250 + "@a.co"],
)
def test_invalid_email_is_rejected(email):
    with pytest.raises(ValueError, match="valid email"):
        _validate_registration(email, "password123")


def test_short_password_is_rejected():
    with pytest.raises(ValueError, match="at least"):
        _validate_registration("person@example.com", "short")


def test_overlong_password_is_rejected():
    with pytest.raises(ValueError, match="at most"):
        _validate_registration("person@example.com", "p" * 129)


def test_non_string_password_is_rejected():
    with pytest.raises(ValueError):
        _validate_registration("person@example.com", None)


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_secret_key_is_rejected(monkeypatch, value):
    monkeypatch.setenv("JWT_SECRET_KEY", value)

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        create_token(User(email="a@example.com"))


def test_missing_secret_key_is_rejected(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        create_token(User(email="a@example.com"))

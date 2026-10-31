import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt


DEFAULT_TOKEN_LIFETIME_MINUTES = 60 * 24
MIN_SECRET_KEY_LENGTH = 32


def _get_secret_key() -> str:
    secret_key = os.environ.get("JWT_SECRET_KEY", "")

    if not secret_key.strip():
        raise RuntimeError(
            "JWT_SECRET_KEY must be set to a non-empty value."
        )

    if len(secret_key.strip()) < MIN_SECRET_KEY_LENGTH:
        raise RuntimeError(
            f"JWT_SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} "
            "characters. Generate one with: "
            'python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )

    return secret_key


def _get_token_lifetime() -> timedelta:
    """Return the token lifetime, configurable with JWT_EXPIRES_MINUTES."""
    raw_value = os.environ.get("JWT_EXPIRES_MINUTES")

    if raw_value is None:
        return timedelta(minutes=DEFAULT_TOKEN_LIFETIME_MINUTES)

    try:
        minutes = int(raw_value)
    except ValueError as error:
        raise RuntimeError(
            "JWT_EXPIRES_MINUTES must be a whole number of minutes."
        ) from error

    if minutes <= 0:
        raise RuntimeError("JWT_EXPIRES_MINUTES must be greater than zero.")

    return timedelta(minutes=minutes)


def create_token(user) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": now + _get_token_lifetime(),
    }

    return jwt.encode(
        payload,
        _get_secret_key(),
        algorithm="HS256",
    )


def decode_token(token: str) -> UUID:
    """Return the user ID from a valid, unexpired token.

    Raises jwt.InvalidTokenError (including jwt.ExpiredSignatureError)
    for any token that cannot be trusted.
    """
    payload = jwt.decode(
        token,
        _get_secret_key(),
        algorithms=["HS256"],
        options={"require": ["exp", "sub"]},
    )

    try:
        return UUID(payload["sub"])
    except (ValueError, TypeError, AttributeError) as error:
        raise jwt.InvalidTokenError("Invalid token subject.") from error

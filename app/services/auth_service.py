import re

from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.services.password_service import (
    hash_password,
    verify_password
)
from app.services.token_service import create_token


# Checked when the email is unknown, so a missing account takes about as long
# to reject as a wrong password and the response time does not reveal which
# emails are registered.
_UNKNOWN_USER_HASH = hash_password("not-a-real-password")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_EMAIL_LENGTH = 254
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def _validate_registration(email, password) -> None:
    if (
        not isinstance(email, str)
        or len(email) > MAX_EMAIL_LENGTH
        or not EMAIL_PATTERN.match(email)
    ):
        raise ValueError("A valid email address is required.")

    if not isinstance(password, str):
        raise ValueError("A valid password is required.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        )

    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at most {MAX_PASSWORD_LENGTH} characters."
        )


class AuthService:
    def __init__(self, repository):
        self.repository = repository

    def register(self, email: str, password: str) -> User:
        _validate_registration(email, password)

        user = User(
            email=email,
            password_hash=hash_password(password),
        )

        try:
            self.repository.save(user)
        except IntegrityError as error:
            self.repository.session.rollback()

            if "users_email_key" in str(error.orig):
                raise ValueError("Email is already registered.") from error

            raise

        return user

    def login(self, email: str, password: str) -> User:
        user = self.repository.find_by_email(email)

        if user is None:
            verify_password(password, _UNKNOWN_USER_HASH)
            raise ValueError("Invalid email or password.")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password.")

        return {
            "user_id": user.id,
            "token": create_token(user),
        }
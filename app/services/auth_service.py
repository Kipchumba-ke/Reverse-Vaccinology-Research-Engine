from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.services.password_service import (
    hash_password,
    verify_password
)
from app.services.token_service import create_token


class AuthService:
    def __init__(self, repository):
        self.repository = repository

    def register(self, email: str, password: str) -> User:
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
            raise ValueError("Invalid email or password.")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password.")

        return {
            "user_id": user.id,
            "token": create_token(user),
        }
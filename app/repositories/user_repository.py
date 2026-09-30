from app.models.user import User
from app.models.user_orm import UserModel


class UserRepository:
    def __init__(self, session):
        self.session = session

    @staticmethod
    def _to_orm(user):
        return UserModel(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
        )

    @staticmethod
    def _to_domain(model):
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
        )

    def save(self, user):
        model = self._to_orm(user)
        self.session.add(model)
        self.session.flush()
        return user

    def find_by_id(self, user_id):
        model = self.session.get(UserModel, user_id)

        if model is None:
            return None

        return self._to_domain(model)

    def find_by_email(self, email):
        model = (
            self.session.query(UserModel)
            .filter(UserModel.email == email)
            .first()
        )

        if model is None:
            return None

        return self._to_domain(model)
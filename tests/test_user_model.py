import jwt

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.password_service import (
        hash_password,
        verify_password,
    )
from app.services.auth_service import AuthService
from app.services.token_service import (
    create_token,
    decode_token,
)


def test_user_has_identity_and_password_hash():
    user = User(
        email="kelvin@example.com",
        password_hash="hashed-password",
    )

    assert user.id is not None
    assert user.email == "kelvin@example.com"
    assert user.password_hash == "hashed-password"



def test_user_repository_saves_and_finds_user(db_session):

    repository = UserRepository(db_session)

    user = User(
        email="kelvin@example.com",
        password_hash="hashed-password",
    )

    repository.save(user)
    db_session.commit()

    saved_user = repository.find_by_id(user.id)

    assert saved_user is not None
    assert saved_user.id == user.id
    assert saved_user.email == "kelvin@example.com"
    assert saved_user.password_hash == "hashed-password"



def test_user_password_is_hashed():

    password = "StrongPassword123!"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash



def test_password_hash_can_be_verified():

    password = "StrongPassword123!"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True
    assert verify_password("WrongPassword123!", password_hash) is False



def test_registration_creates_user_with_hashed_password(db_session):

    repository = UserRepository(db_session)
    service = AuthService(repository)

    user = service.register(
        email="new-user@example.com",
        password="StrongPassword123!",
    )

    assert user.id is not None
    assert user.email == "new-user@example.com"
    assert user.password_hash != "StrongPassword123!"
    assert user.password_hash



def test_registration_rejects_duplicate_email(db_session):

    repository = UserRepository(db_session)
    service = AuthService(repository)

    service.register(
        email="duplicate@example.com",
        password="StrongPassword123!",
    )

    db_session.commit()

    try:
        service.register(
            email="duplicate@example.com",
            password="AnotherPassword123!",
        )
        assert False, "Expected duplicate email to be rejected."
    except ValueError as error:
        assert str(error) == "Email is already registered."



def test_login_returns_user_for_valid_credentials(db_session):

    repository = UserRepository(db_session)
    service = AuthService(repository)

    registered_user = service.register(
        email="login@example.com",
        password="StrongPassword123!",
    )

    db_session.commit()

    authenticated_user = service.login(
        email="login@example.com",
        password="StrongPassword123!",
    )

    assert authenticated_user is not None
    assert authenticated_user["user_id"] == registered_user.id
    assert authenticated_user["token"]



def test_login_rejects_invalid_password(db_session):

    repository = UserRepository(db_session)
    service = AuthService(repository)

    service.register(
        email="invalid-login@example.com",
        password="StrongPassword123!",
    )

    db_session.commit()

    try:
        service.login(
            email="invalid-login@example.com",
            password="WrongPassword123!",
        )
        assert False, "Expected invalid credentials to be rejected."
    except ValueError as error:
        assert str(error) == "Invalid email or password."



def test_login_rejects_unknown_email(db_session):

    repository = UserRepository(db_session)
    service = AuthService(repository)

    try:
        service.login(
            email="does-not-exist@example.com",
            password="StrongPassword123!",
        )
        assert False, "Expected unknown email to be rejected."
    except ValueError as error:
        assert str(error) == "Invalid email or password."



def test_authenticated_user_has_identity(db_session):

    repository = UserRepository(db_session)
    service = AuthService(repository)

    registered_user = service.register(
        email="identity@example.com",
        password="StrongPassword123!",
    )

    db_session.commit()

    authenticated_user = service.login(
        email="identity@example.com",
        password="StrongPassword123!",
    )

    assert authenticated_user["user_id"] == registered_user.id



def test_login_returns_authentication_token(db_session):

    repository = UserRepository(db_session)
    service = AuthService(repository)

    service.register(
        email="token@example.com",
        password="StrongPassword123!",
    )

    db_session.commit()

    result = service.login(
        email="token@example.com",
        password="StrongPassword123!",
    )

    assert result["user_id"] is not None
    assert result["token"]



def test_token_service_creates_token_for_user():
    
    user = User(
        email="token@example.com",
        password_hash="hashed-password",
    )

    token = create_token(user)

    assert token



def test_token_service_recovers_user_id():

    user = User(
        email="token@example.com",
        password_hash="hashed-password",
    )

    token = create_token(user)
    user_id = decode_token(token)

    assert user_id == user.id



def test_token_service_rejects_tampered_token():

    user = User(
        email="tampered@example.com",
        password_hash="hashed-password",
    )

    token = create_token(user)

    header, payload, signature = token.split(".")
    tampered_token = f"{header}.{payload}tampered.{signature}"

    try:
        decode_token(tampered_token)
        assert False, "Expected tampered token to be rejected."
    except jwt.InvalidTokenError:
        pass

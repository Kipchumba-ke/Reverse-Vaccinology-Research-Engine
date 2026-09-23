import pytest

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.database import (
    create_engine,
    create_session_factory,
    create_database_engine_from_environment
)


def test_create_engine_returns_sqlalchemy_engine():
    engine = create_engine(
        "postgresql+psycopg://user:password@localhost/reverse_vaccinology"
    )

    assert isinstance(engine, Engine)

def test_create_session_factory_returns_session_factory():
    engine = create_engine(
        "postgresql+psycopg://user:password@localhost/reverse_vaccinology"
    )

    session_factory = create_session_factory(engine)
    session = session_factory()

    assert isinstance(session, Session)

    session.close()


def test_create_session_factory_disables_autoflush():
    engine = create_engine(
        "postgresql+psycopg://user:password@localhost/reverse_vaccinology"
    )

    session_factory = create_session_factory(engine)
    session = session_factory()

    assert session.autoflush is False

    session.close()


def test_create_database_engine_from_environment(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@localhost/reverse_vaccinology",
    )

    engine = create_database_engine_from_environment()

    assert engine.url.drivername == "postgresql+psycopg"
    assert engine.url.database == "reverse_vaccinology"


def test_create_database_engine_requires_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(KeyError):
        create_database_engine_from_environment()
from sqlalchemy import Engine

from app.database import create_engine


def test_create_engine_returns_sqlalchemy_engine():
    engine = create_engine(
        "postgresql+psycopg://user:password@localhost/reverse_vaccinology"
    )

    assert isinstance(engine, Engine)
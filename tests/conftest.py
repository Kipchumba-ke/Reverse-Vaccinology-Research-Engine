import os

import pytest

from app.database import create_engine, create_session_factory


@pytest.fixture
def db_session():
    database_url = os.environ["DATABASE_URL"]

    engine = create_engine(database_url)
    session_factory = create_session_factory(engine)
    session = session_factory()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()
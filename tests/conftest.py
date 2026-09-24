import os

import pytest
from sqlalchemy import event

from app.database import create_engine, create_session_factory
from app import create_app
from app.repositories.analysis_repository import AnalysisRepository


@pytest.fixture
def db_session():
    database_url = os.environ["DATABASE_URL"]

    engine = create_engine(database_url)
    connection = engine.connect()
    transaction = connection.begin()

    session_factory = create_session_factory(connection)
    session = session_factory()

    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    try:
        yield session
    finally:
        session.close()

        if transaction.is_active:
            transaction.rollback()

        connection.close()
        engine.dispose()

@pytest.fixture
def api_client(db_session):
    repository = AnalysisRepository(db_session)
    app = create_app(repository=repository)
    return app.test_client()

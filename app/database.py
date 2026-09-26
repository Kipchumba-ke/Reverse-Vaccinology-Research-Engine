import os

from dotenv import load_dotenv
from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


load_dotenv()

class Base(DeclarativeBase):
    pass

def create_engine(database_url: str):
    return sqlalchemy_create_engine(database_url)

def create_session_factory(engine):
    return sessionmaker(
        bind=engine,
        autoflush=False,
    )

def create_database_engine_from_environment():
    database_url = os.environ["DATABASE_URL"]
    return create_engine(database_url)
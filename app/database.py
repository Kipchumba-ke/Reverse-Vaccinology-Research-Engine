from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

def create_engine(database_url: str):
    return sqlalchemy_create_engine(database_url)
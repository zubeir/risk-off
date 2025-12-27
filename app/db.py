from __future__ import annotations

from sqlmodel import SQLModel, Session, create_engine


def create_db_engine(sqlite_path: str):
    return create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})


def init_db(engine) -> None:
    SQLModel.metadata.create_all(engine)


def get_session(engine):
    return Session(engine)

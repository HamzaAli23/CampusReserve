import os
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine


def database_url() -> str:
    return os.getenv("CAMPUSRESERVE_DATABASE_URL", "sqlite:///campusreserve.db")


def make_engine(url: str | None = None):
    selected = url or database_url()
    connect_args = {"check_same_thread": False} if selected.startswith("sqlite") else {}
    return create_engine(selected, connect_args=connect_args)


engine = make_engine()


def create_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


"""SQLite via SQLAlchemy. The DB file lives under the Takt-Harness data tree
(guard-checked at startup), so all persistence is write-scoped by construction.
"""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings
from .guard import assert_db_path_scoped


class Base(DeclarativeBase):
    pass


assert_db_path_scoped()  # fail fast if the DB path is misconfigured
engine = create_engine(
    settings.db_url, connect_args={"check_same_thread": False}, future=True
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)


def init_db() -> None:
    from . import models  # noqa: F401  (register mappers)

    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

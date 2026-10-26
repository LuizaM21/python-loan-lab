"""Engine and session setup."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

IN_MEMORY = {"sqlite://", "sqlite:///:memory:"}


def make_engine(url: str) -> Engine:
    if not url.startswith("sqlite"):
        return create_engine(url, pool_pre_ping=True)

    kwargs: dict[str, Any] = {"connect_args": {"check_same_thread": False, "timeout": 15}}
    if url in IN_MEMORY:
        # One shared connection. Without it, every new connection sees an empty database.
        kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **kwargs)

    # SQLAlchemy's documented recipe: let SQLAlchemy emit BEGIN so SAVEPOINTs work,
    # and switch on foreign keys (SQLite ignores them by default).
    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection, _record):
        dbapi_connection.isolation_level = None
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    @event.listens_for(engine, "begin")
    def _on_begin(connection):
        connection.exec_driver_sql("BEGIN")

    return engine


def make_sessionmaker(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False)

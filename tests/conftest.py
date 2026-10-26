"""Shared fixtures. pytest finds this file by name; tests ask for fixtures by argument name."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date

import pytest
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from loanlab.api import create_app
from loanlab.db import make_engine, make_sessionmaker
from loanlab.events import InMemoryEventLog
from loanlab.models import Base
from loanlab.services import LoanService

FIXED_TODAY = date(2026, 3, 1)
API_KEY = "lab-dev-key"


# ----------------------------------------------------------------------------- unit level


@pytest.fixture
def session() -> Iterator[Session]:
    """A fresh in-memory database for every test: tests never see each other's data."""
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    with make_sessionmaker(engine)() as session:
        yield session
    engine.dispose()


@pytest.fixture
def events() -> InMemoryEventLog:
    return InMemoryEventLog()


@pytest.fixture
def service(session: Session, events: InMemoryEventLog) -> LoanService:
    """The service with a fixed date. Never depend on the real date in a test."""
    return LoanService(session, events, today=lambda: FIXED_TODAY)


# ----------------------------------------------------------------------------- API level


@pytest.fixture(scope="module")
def client() -> Iterator[FlaskClient]:
    """One app per test module, shared by its tests (like a real server).

    Because the data is shared, never assert exact list counts. Use unique names.
    """
    app = create_app(
        {"TESTING": True, "DATABASE_URL": "sqlite://", "LOG_LEVEL": "WARNING", "MONGO_URL": ""},
        today=lambda: FIXED_TODAY,
    )
    yield app.test_client()
    app.extensions["loanlab.engine"].dispose()


@pytest.fixture
def write_headers() -> dict[str, str]:
    return {"X-Api-Key": API_KEY}

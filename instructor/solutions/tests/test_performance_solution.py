"""Reference: catch N+1 queries with an SQLAlchemy event listener instead of waiting for production."""

from contextlib import contextmanager
from decimal import Decimal

from sqlalchemy import event

from loanlab.api import create_app
from loanlab.events import InMemoryEventLog
from loanlab.seed import seed_demo


@contextmanager
def count_selects(engine):
    statements: list[str] = []

    def log(conn, cursor, statement, *args):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", log)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", log)


def make_app(loans: int):
    events = InMemoryEventLog()
    app = create_app({"TESTING": True, "DATABASE_URL": "sqlite://", "LOG_LEVEL": "WARNING"}, events=events)
    with app.extensions["loanlab.sessionmaker"]() as session:
        seed_demo(session, events, loans)
    return app


class TestQueryCounts:
    def test_listing_100_loans_takes_a_constant_number_of_queries(self):
        app = make_app(120)
        client = app.test_client()
        with count_selects(app.extensions["loanlab.engine"]) as selects:
            response = client.get("/api/loans?size=100")
        assert response.status_code == 200
        assert len(response.get_json()["items"]) == 100
        assert len(selects) <= 3, f"{len(selects)} SELECTs: N+1?"

    def test_portfolio_stats_are_right(self):
        # Expected values worked out from the two seeded loans plus one repayment.
        app = create_app({"TESTING": True, "DATABASE_URL": "sqlite://", "LOG_LEVEL": "WARNING"})
        client = app.test_client()
        client.post(
            "/api/loans/1/repayments",
            json={"amount": "500.00"},
            headers={"X-Api-Key": "lab-dev-key", "Idempotency-Key": "stats-1"},
        )
        assert client.get("/api/stats/portfolio").get_json() == {
            "activeLoans": 2,
            "totalOutstanding": "79500.00",
            "totalRepaid": "500.00",
            "byProduct": [
                {"productCode": "AUTO", "activeLoans": 1, "outstanding": "60000.00"},
                {"productCode": "PERS", "activeLoans": 1, "outstanding": "19500.00"},
            ],
        }
        assert Decimal("79500.00") == Decimal("60000.00") + Decimal("19500.00")

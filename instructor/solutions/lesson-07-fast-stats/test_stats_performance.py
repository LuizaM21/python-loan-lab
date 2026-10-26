"""Lesson 07 reference tests. The first test pins the OUTPUT before optimising; the second pins the COST.
Copy into tests/api."""

from contextlib import contextmanager

from sqlalchemy import event

from loanlab.api import create_app
from loanlab.events import InMemoryEventLog
from loanlab.seed import seed_demo
from loanlab.stats import portfolio_stats


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


def demo_app(loans: int):
    events = InMemoryEventLog()
    app = create_app({"TESTING": True, "DATABASE_URL": "sqlite://", "LOG_LEVEL": "WARNING"}, events=events)
    with app.extensions["loanlab.sessionmaker"]() as session:
        seed_demo(session, events, loans)
    return app


class TestPortfolioStats:
    def test_output_on_known_data(self):
        # 2 seeded loans + 200 demo loans. Golden values captured from the SLOW version before changing it:
        # "characterization test" -- the refactor must not change a single digit.
        app = demo_app(200)
        with app.extensions["loanlab.sessionmaker"]() as session:
            stats = portfolio_stats(session)
        assert stats == {
            "activeLoans": 194,
            "totalOutstanding": "22300300.00",
            "totalRepaid": "1330400.00",
            "byProduct": [
                {"productCode": "AUTO", "activeLoans": 54, "outstanding": "4148900.00"},
                {"productCode": "HOME", "activeLoans": 61, "outstanding": "16133700.00"},
                {"productCode": "PERS", "activeLoans": 79, "outstanding": "2017700.00"},
            ],
        }

    def test_query_count_does_not_grow_with_the_number_of_loans(self):
        app = demo_app(300)
        with (
            app.extensions["loanlab.sessionmaker"]() as session,
            count_selects(app.extensions["loanlab.engine"]) as selects,
        ):
            portfolio_stats(session)
        assert len(selects) <= 3, f"{len(selects)} SELECTs"

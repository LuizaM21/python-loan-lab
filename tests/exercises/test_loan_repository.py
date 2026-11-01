from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from exercises.loan_repository import LoanRepository
from loanlab.services import LoanService

pytestmark = pytest.mark.exercise


@contextmanager
def count_queries(session: Session) -> Iterator[list[str]]:
    """Collect every SQL statement the session's engine runs inside the block."""
    statements: list[str] = []
    engine = session.get_bind()

    def listener(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", listener)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", listener)


def selects(statements: list[str]) -> list[str]:
    return [s for s in statements if s.lstrip().upper().startswith("SELECT")]


@pytest.fixture
def repo(session: Session) -> LoanRepository:
    return LoanRepository(session)


def open_and_close(service: LoanService, name: str, key: str) -> None:
    loan = service.open_loan(name, "PERS", Decimal("1000.00"), 6)
    service.repay(loan.id, loan.outstanding, key)


class TestFindByReference:
    def test_finds_a_loan_by_reference(self, service, repo):
        service.open_loan("Ana Pop", "PERS", Decimal("10000.00"), 12)

        assert repo.find_by_reference("LN-0001").customer_name == "Ana Pop"

    def test_returns_none_for_an_unknown_reference(self, repo):
        assert repo.find_by_reference("LN-9999") is None


class TestCounting:
    def test_counts_only_active_loans_matching_the_name_loosely(self, service, repo, session):
        # setup

        service.open_loan("Ana Pop", "PERS", Decimal("10000.00"), 12)
        service.open_loan("Ana Pop", "AUTO", Decimal("20000.00"), 24)
        service.open_loan("Ion Rusu", "PERS", Decimal("10000.00"), 12)
        open_and_close(service, "Ana Pop", "close-1")

        # execute

        with count_queries(session) as statements:
            active = repo.count_active_for("  ANA POP ")

        # verify

        assert active == 2
        assert len(selects(statements)) == 1
        assert "count(" in selects(statements)[0].lower()

    def test_counts_all_loans_including_closed(self, service, repo):
        service.open_loan("Ana Pop", "PERS", Decimal("10000.00"), 12)
        open_and_close(service, "Ana Pop", "close-1")

        assert repo.count_all_for("ana pop") == 2

    def test_zero_for_a_new_customer(self, repo):
        assert repo.count_active_for("Nobody Yet") == 0
        assert repo.count_all_for("Nobody Yet") == 0


class TestWithRepayments:
    def test_loads_loans_and_repayments_in_two_queries(self, service, repo, session):
        # setup

        for n in range(20):
            loan = service.open_loan(f"Customer {n}", "PERS", Decimal("5000.00"), 12)
            service.repay(loan.id, Decimal("100.00"), f"pay-{n}")
        session.commit()
        session.expunge_all()  # empty the identity map: no free lunch from objects already in memory

        # execute

        with count_queries(session) as statements:
            loans = repo.with_repayments()
            repaid = [r.amount for loan in loans for r in loan.repayments]

        # verify

        assert len(loans) == 20
        assert [loan.id for loan in loans] == sorted(loan.id for loan in loans)
        assert repaid == [Decimal("100.00")] * 20
        assert len(selects(statements)) == 2

    def test_filters_by_status(self, service, repo):
        service.open_loan("Ana Pop", "PERS", Decimal("10000.00"), 12)
        open_and_close(service, "Ion Rusu", "close-1")

        assert [loan.customer_name for loan in repo.with_repayments(status="closed")] == ["Ion Rusu"]


class TestOutstandingByProduct:
    def test_sums_active_outstanding_per_product_in_one_query(self, service, repo, session):
        # setup

        service.open_loan("Ana Pop", "PERS", Decimal("10000.00"), 12)
        pers = service.open_loan("Ion Rusu", "PERS", Decimal("5000.50"), 12)
        service.repay(pers.id, Decimal("0.25"), "pay-1")
        service.open_loan("Elena Matei", "AUTO", Decimal("60000.00"), 48)
        open_and_close(service, "Vlad Ilie", "close-1")  # closed: not counted

        # execute

        with count_queries(session) as statements:
            result = repo.outstanding_by_product()

        # verify

        assert result == {"AUTO": Decimal("60000.00"), "PERS": Decimal("15000.25")}
        assert len(selects(statements)) == 1
        assert "group by" in selects(statements)[0].lower()

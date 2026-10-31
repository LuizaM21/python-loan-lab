"""Lesson 16 exercise: a repository over the SQLAlchemy ORM.

Tests: tests/exercises/test_loan_repository.py   Run: pytest -m exercise tests/exercises/test_loan_repository.py

A Repository hides HOW loans are stored behind methods named in the domain's language. The service
and the eligibility rules then depend on "count the active loans of a customer", not on SELECTs.

Write LoanRepository(session) with:

- find_by_reference(reference) -> Loan | None
- count_active_for(customer_name) -> int
    Active loans only. The name is matched trimmed and case-insensitively (" ANA POP" finds "Ana Pop").
    One SELECT COUNT(*) query: never load the rows to count them in Python.
- count_all_for(customer_name) -> int
    Active and closed. Same matching. (FirstLoanCap from lesson 12 needs this.)
- with_repayments(status=None) -> list[Loan]
    Loans in id order, each with `repayments` already loaded. EXACTLY 2 queries however many loans
    there are (selectinload). Accessing loan.repayments afterwards must not run any query.
- outstanding_by_product() -> dict[str, Decimal]
    Active loans only: {"AUTO": Decimal("60000.00"), "PERS": ...}, computed by the DATABASE in ONE
    query (GROUP BY), every value rounded to 0.01. Products without active loans are absent.

Rules: the repository never commits (the caller owns the transaction, like the service). Use 2.0
style: select(...), session.scalars / session.scalar / session.execute.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from loanlab.models import Loan


class LoanRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_reference(self, reference: str) -> Loan | None:
        raise NotImplementedError  # TODO lesson 16

    def count_active_for(self, customer_name: str) -> int:
        raise NotImplementedError  # TODO lesson 16

    def count_all_for(self, customer_name: str) -> int:
        raise NotImplementedError  # TODO lesson 16

    def with_repayments(self, status: str | None = None) -> list[Loan]:
        raise NotImplementedError  # TODO lesson 16

    def outstanding_by_product(self) -> dict[str, Decimal]:
        raise NotImplementedError  # TODO lesson 16

"""Reference solution, lesson 16: repository over the ORM."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from loanlab.models import Loan
from loanlab.money import to_money


def _name_matches(customer_name: str):
    # func.lower on both sides: case-insensitive on SQLite and PostgreSQL alike.
    # (In PostgreSQL, a functional index on lower(customer_name) keeps it fast.)
    return func.lower(Loan.customer_name) == customer_name.strip().lower()


class LoanRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_reference(self, reference: str) -> Loan | None:
        return self._session.scalars(select(Loan).where(Loan.reference == reference)).one_or_none()

    def count_active_for(self, customer_name: str) -> int:
        query = select(func.count()).select_from(Loan).where(_name_matches(customer_name), Loan.status == "active")
        return self._session.scalar(query) or 0

    def count_all_for(self, customer_name: str) -> int:
        return self._session.scalar(select(func.count()).select_from(Loan).where(_name_matches(customer_name))) or 0

    def with_repayments(self, status: str | None = None) -> list[Loan]:
        query = select(Loan).options(selectinload(Loan.repayments)).order_by(Loan.id)
        if status is not None:
            query = query.where(Loan.status == status)
        return list(self._session.scalars(query).all())

    def outstanding_by_product(self) -> dict[str, Decimal]:
        query = (
            select(Loan.product_code, func.sum(Loan.outstanding))
            .where(Loan.status == "active")
            .group_by(Loan.product_code)
            .order_by(Loan.product_code)
        )
        return {code: to_money(Decimal(str(total))) for code, total in self._session.execute(query)}

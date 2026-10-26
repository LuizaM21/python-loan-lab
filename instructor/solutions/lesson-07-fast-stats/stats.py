"""Lesson 07 reference solution: replaces loanlab/stats.py. Same output, 2 queries for any number of loans.

Before: 1 + 2 x N queries (one get() and one lazy load of repayments per loan) and every row
pulled into Python. After: the database does the grouping and summing.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from loanlab.models import Loan, Repayment
from loanlab.money import format_money


def portfolio_stats(session: Session) -> dict:
    rows = session.execute(
        select(Loan.product_code, func.count(Loan.id), func.sum(Loan.outstanding))
        .where(Loan.status == "active")
        .group_by(Loan.product_code)
        .order_by(Loan.product_code)
    ).all()
    total_repaid = session.scalar(select(func.sum(Repayment.amount))) or Decimal("0")

    by_product = [
        {"productCode": code, "activeLoans": count, "outstanding": format_money(Decimal(outstanding))}
        for code, count, outstanding in rows
    ]
    return {
        "activeLoans": sum(count for _, count, _ in rows),
        "totalOutstanding": format_money(sum((Decimal(o) for _, _, o in rows), Decimal("0"))),
        "totalRepaid": format_money(Decimal(total_repaid)),
        "byProduct": by_product,
    }

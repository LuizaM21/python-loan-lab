"""Portfolio statistics for GET /api/stats/portfolio.

Lesson 07: this function is CORRECT but SLOW. With a few thousand loans it issues thousands of
queries. Measure it first (k6 + the query counter), then fix it. Keep the output identical.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Loan
from .money import format_money


def portfolio_stats(session: Session) -> dict:
    by_product: dict[str, dict] = {}
    total_outstanding = Decimal("0")
    total_repaid = Decimal("0")
    active_loans = 0

    loan_ids = session.scalars(select(Loan.id).order_by(Loan.id)).all()
    for loan_id in loan_ids:
        loan = session.get_one(Loan, loan_id)
        repaid = sum((r.amount for r in loan.repayments), Decimal("0"))
        total_repaid += repaid
        if loan.status != "active":
            continue
        active_loans += 1
        total_outstanding += loan.outstanding
        entry = by_product.setdefault(loan.product_code, {"activeLoans": 0, "outstanding": Decimal("0")})
        entry["activeLoans"] += 1
        entry["outstanding"] += loan.outstanding

    return {
        "activeLoans": active_loans,
        "totalOutstanding": format_money(total_outstanding),
        "totalRepaid": format_money(total_repaid),
        "byProduct": [
            {"productCode": code, "activeLoans": e["activeLoans"], "outstanding": format_money(e["outstanding"])}
            for code, e in sorted(by_product.items())
        ],
    }

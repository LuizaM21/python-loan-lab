"""Extract data back OUT of the database: a loan report for the finance team. Lesson 17.

Two things to notice:
1. One SQL query for the whole report. "Repaid so far" is a SUM per loan, computed by the database
   in a subquery and joined in (LEFT OUTER JOIN: loans without repayments still appear, with 0).
   Compare with stats.py before lesson 07: one query per loan.
2. Streaming. `yield_per` fetches rows in batches and this function is a generator, so a report of
   a million loans uses the memory of one batch, and the first CSV line goes out immediately.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Iterator
from typing import TextIO

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Loan, Repayment
from ..money import format_money

REPORT_COLUMNS = (
    "reference",
    "customerName",
    "productCode",
    "amount",
    "repaid",
    "outstanding",
    "status",
    "createdOn",
)


def loan_report_rows(session: Session, status: str | None = None, batch_size: int = 500) -> Iterator[dict[str, str]]:
    repaid = (
        select(Repayment.loan_id, func.sum(Repayment.amount).label("repaid")).group_by(Repayment.loan_id).subquery()
    )
    statement = (
        select(
            Loan.reference,
            Loan.customer_name,
            Loan.product_code,
            Loan.amount,
            func.coalesce(repaid.c.repaid, 0).label("repaid"),
            Loan.outstanding,
            Loan.status,
            Loan.created_on,
        )
        .outerjoin(repaid, repaid.c.loan_id == Loan.id)
        .order_by(Loan.id)
        .execution_options(yield_per=batch_size)
    )
    if status is not None:
        statement = statement.where(Loan.status == status)

    for row in session.execute(statement):
        yield {
            "reference": row.reference or "",
            "customerName": row.customer_name,
            "productCode": row.product_code,
            "amount": format_money(row.amount),
            "repaid": format_money(row.repaid),
            "outstanding": format_money(row.outstanding),
            "status": row.status,
            "createdOn": row.created_on.isoformat(),
        }


def write_csv(rows: Iterable[dict[str, str]], out: TextIO) -> int:
    """Write the rows with a header line. Returns how many data rows were written."""
    writer = csv.DictWriter(out, fieldnames=REPORT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    count = 0
    for row in rows:
        writer.writerow(row)
        count += 1
    return count

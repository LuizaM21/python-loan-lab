"""Start-up data: two sample loans, plus optional demo volume for performance work."""

from __future__ import annotations

import random
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .events import EventLog
from .models import Loan
from .services import LoanService

FIRST_NAMES = ["Ana", "Ion", "Maria", "Andrei", "Elena", "Mihai", "Ioana", "Radu", "Irina", "Vlad"]
LAST_NAMES = ["Pop", "Ionescu", "Stan", "Popescu", "Dumitru", "Rusu", "Matei", "Ilie", "Lungu", "Moraru"]


def seed(session: Session, events: EventLog) -> None:
    """The two sample loans: LN-0001 and LN-0002. Runs only on an empty database."""
    if session.scalar(select(func.count()).select_from(Loan)):
        return
    LoanService(session, events, today=lambda: date(2026, 1, 15)).open_loan(
        "Maria Ionescu", "PERS", Decimal("20000.00"), 24
    )
    LoanService(session, events, today=lambda: date(2026, 2, 3)).open_loan(
        "Andrei Stan", "AUTO", Decimal("60000.00"), 48
    )
    session.commit()


def seed_demo(session: Session, events: EventLog, count: int) -> None:
    """`count` random loans, about a third with a repayment and a few closed. Same data every time."""
    rng = random.Random(42)
    service = LoanService(session, events, today=lambda: date(2026, 3, 1))
    terms = {"PERS": (1000, 50000, 6, 60), "AUTO": (5000, 150000, 12, 84), "HOME": (20000, 500000, 60, 360)}
    for n in range(count):
        code = rng.choice(list(terms))
        low, high, min_m, max_m = terms[code]
        loan = service.open_loan(
            f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
            code,
            Decimal(rng.randrange(low, high, 100)),
            rng.randint(min_m, max_m),
        )
        if n % 3 == 0:
            service.repay(loan.id, Decimal("100.00"), f"demo-{n}-a")
        if n % 25 == 0:
            service.repay(loan.id, loan.outstanding, f"demo-{n}-b")
        if n % 500 == 0:
            session.commit()
    session.commit()

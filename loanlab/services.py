"""Use cases. The service validates, changes data and records events.

It never commits: the caller (one HTTP request, one test) owns the transaction.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import schedule
from .errors import Conflict, NotFound, ValidationError
from .events import EventLog
from .models import Loan, Repayment
from .money import format_money, has_at_most_two_decimals
from .products import LoanProduct, all_products, find_product

MAX_CUSTOMER_NAME = 100
MAX_IDEMPOTENCY_KEY = 64
STATUSES = ("active", "closed")


class LoanService:
    def __init__(self, session: Session, events: EventLog, today: Callable[[], date] = date.today):
        self._session = session
        self._events = events
        self._today = today

    # ------------------------------------------------------------------ products and quotes

    def products(self) -> list[LoanProduct]:
        return all_products()

    def quote(self, product_code: str | None, amount: Decimal, months: int) -> tuple[LoanProduct, schedule.Schedule]:
        product = self._validate_terms(product_code, amount, months)
        return product, schedule.calculate(amount, product.annual_rate, months)

    # ------------------------------------------------------------------ loans

    def open_loan(self, customer_name: str | None, product_code: str | None, amount: Decimal, months: int) -> Loan:
        name = (customer_name or "").strip()
        if not name:
            raise ValidationError("Customer name is required.")
        if len(name) > MAX_CUSTOMER_NAME:
            raise ValidationError("Customer name must be 100 characters or fewer.")
        product = self._validate_terms(product_code, amount, months)

        loan = Loan(
            customer_name=name,
            product_code=product.code,
            amount=amount,
            annual_rate=product.annual_rate,
            months=months,
            monthly_payment=schedule.monthly_payment(amount, product.annual_rate, months),
            outstanding=amount,
            status="active",
            created_on=self._today(),
        )
        self._session.add(loan)
        self._session.flush()  # the database assigns loan.id
        loan.reference = f"LN-{loan.id:04d}"
        self._session.flush()

        self._events.record(
            "loan_opened",
            loan.reference,
            {"customerName": name, "productCode": product.code, "amount": format_money(amount), "months": months},
        )
        return loan

    def get_loan(self, loan_id: int) -> Loan:
        loan = self._session.get(Loan, loan_id)
        if loan is None:
            raise NotFound("Loan not found.")
        return loan

    def list_loans(self, status: str | None, page: int, size: int) -> tuple[list[Loan], int]:
        if status is not None and status not in STATUSES:
            raise ValidationError("Status must be active or closed.")
        query = select(Loan)
        count = select(func.count()).select_from(Loan)
        if status:
            query = query.where(Loan.status == status)
            count = count.where(Loan.status == status)
        total = self._session.scalar(count) or 0
        loans = self._session.scalars(query.order_by(Loan.id).limit(size).offset((page - 1) * size)).all()
        return list(loans), total

    def schedule_for(self, loan: Loan) -> schedule.Schedule:
        return schedule.calculate(loan.amount, loan.annual_rate, loan.months)

    def history(self, loan: Loan) -> list[dict]:
        return self._events.history(loan.reference or "")

    # ------------------------------------------------------------------ repayments

    def repay(self, loan_id: int, amount: Decimal, idempotency_key: str | None) -> tuple[Repayment, bool]:
        """Returns (repayment, created). A retry with the same key returns the first repayment."""
        key = (idempotency_key or "").strip()
        if not key or len(key) > MAX_IDEMPOTENCY_KEY:
            raise ValidationError("Idempotency-Key header is required (1-64 characters).")
        if amount <= 0:
            raise ValidationError("Repayment amount must be positive.")
        if not has_at_most_two_decimals(amount):
            raise ValidationError("Amount must have at most 2 decimals.")

        existing = self._session.scalars(select(Repayment).where(Repayment.idempotency_key == key)).first()
        if existing is not None:
            if existing.loan_id != loan_id or existing.amount != amount:
                raise Conflict("Idempotency-Key was already used for a different request.")
            return existing, False

        # FOR UPDATE: on PostgreSQL two concurrent repayments wait for each other here.
        loan = self._session.get(Loan, loan_id, with_for_update=True)
        if loan is None:
            raise NotFound("Loan not found.")
        if loan.status == "closed":
            raise Conflict(f"Loan {loan.reference} is closed.")
        if amount > loan.outstanding:
            raise Conflict(f"Repayment exceeds the outstanding balance of {format_money(loan.outstanding)} RON.")

        repayment = Repayment(amount=amount, paid_on=self._today(), idempotency_key=key)
        loan.repayments.append(repayment)
        loan.outstanding -= amount
        if loan.outstanding == 0:
            loan.status = "closed"
        self._session.flush()

        self._events.record("repayment_recorded", loan.reference or "", {"amount": format_money(amount)})
        if loan.status == "closed":
            self._events.record("loan_closed", loan.reference or "", {})
        return repayment, True

    # ------------------------------------------------------------------ validation

    def _validate_terms(self, product_code: str | None, amount: Decimal, months: int) -> LoanProduct:
        product = find_product(product_code)
        if product is None:
            raise ValidationError("Unknown loan product.")
        if not has_at_most_two_decimals(amount):
            raise ValidationError("Amount must have at most 2 decimals.")
        if amount < product.min_amount or amount > product.max_amount:
            raise ValidationError(
                f"Amount must be between {product.min_amount} and {product.max_amount} RON for {product.name}."
            )
        if months < product.min_months or months > product.max_months:
            raise ValidationError(
                f"Term must be between {product.min_months} and {product.max_months} months for {product.name}."
            )
        return product

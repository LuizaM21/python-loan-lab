"""Reading request bodies and writing response bodies. JSON uses camelCase; money is a string."""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any

from flask import request

from ..errors import ValidationError
from ..models import Loan, Repayment
from ..money import format_money
from ..products import LoanProduct, find_product
from ..schedule import Instalment, Schedule

# ----------------------------------------------------------------------------- reading


def json_body() -> dict[str, Any]:
    """Parse the body with parse_float=Decimal: 10000.10 must never pass through a float."""
    try:
        body = json.loads(request.get_data(as_text=True) or "null", parse_float=Decimal)
    except ValueError:
        body = None
    if not isinstance(body, dict):
        raise ValidationError("Request body must be a JSON object.")
    return body


def read_decimal(body: dict[str, Any], field: str, label: str) -> Decimal:
    value = body.get(field)
    if value is None:
        raise ValidationError(f"{label} is required.")
    if isinstance(value, bool):
        raise ValidationError(f"{label} must be a number.")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, (Decimal, str)):
        try:
            number = Decimal(value)
        except InvalidOperation:
            raise ValidationError(f"{label} must be a number.") from None
        if number.is_finite():
            return number
    raise ValidationError(f"{label} must be a number.")


def read_int(body: dict[str, Any], field: str, label: str) -> int:
    value = body.get(field)
    if value is None:
        raise ValidationError(f"{label} is required.")
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{label} must be a whole number.")
    return value


def read_str(body: dict[str, Any], field: str, label: str) -> str | None:
    value = body.get(field)
    if value is not None and not isinstance(value, str):
        raise ValidationError(f"{label} must be text.")
    return value


def query_int(name: str, default: int, maximum: int) -> int:
    raw = request.args.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if not 1 <= value <= maximum:
        raise ValidationError(f"{name} must be a whole number from 1 to {maximum}.")
    return value


# ----------------------------------------------------------------------------- writing


def product_json(product: LoanProduct) -> dict[str, Any]:
    return {
        "code": product.code,
        "name": product.name,
        "annualRate": f"{product.annual_rate:.4f}",
        "minAmount": format_money(product.min_amount),
        "maxAmount": format_money(product.max_amount),
        "minMonths": product.min_months,
        "maxMonths": product.max_months,
    }


def instalment_json(instalment: Instalment) -> dict[str, Any]:
    return {
        "month": instalment.month,
        "payment": format_money(instalment.payment),
        "interest": format_money(instalment.interest),
        "principal": format_money(instalment.principal),
        "balance": format_money(instalment.balance),
    }


def schedule_json(schedule: Schedule) -> dict[str, Any]:
    return {
        "monthlyPayment": format_money(schedule.monthly_payment),
        "instalments": [instalment_json(i) for i in schedule.instalments],
    }


def loan_json(loan: Loan) -> dict[str, Any]:
    product = find_product(loan.product_code)
    return {
        "id": loan.id,
        "reference": loan.reference,
        "customerName": loan.customer_name,
        "productCode": loan.product_code,
        "productName": product.name if product else loan.product_code,
        "amount": format_money(loan.amount),
        "annualRate": f"{loan.annual_rate:.4f}",
        "months": loan.months,
        "monthlyPayment": format_money(loan.monthly_payment),
        "outstanding": format_money(loan.outstanding),
        "status": loan.status,
        "createdOn": loan.created_on.isoformat(),
    }


def repayment_json(repayment: Repayment) -> dict[str, Any]:
    return {
        "id": repayment.id,
        "loanId": repayment.loan_id,
        "amount": format_money(repayment.amount),
        "paidOn": repayment.paid_on.isoformat(),
    }


def event_json(event: dict[str, Any]) -> dict[str, Any]:
    at = event["at"]
    return {
        "type": event["type"],
        "loanReference": event["loanReference"],
        "at": at.isoformat(timespec="milliseconds") + "Z" if hasattr(at, "isoformat") else at,
        "data": event.get("data", {}),
    }

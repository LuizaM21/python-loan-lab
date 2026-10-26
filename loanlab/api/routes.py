"""HTTP endpoints. Thin: read the request, call the service, write the response."""

from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request, url_for
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..services import LoanService
from ..stats import portfolio_stats
from .auth import require_api_key
from .payloads import (
    event_json,
    json_body,
    loan_json,
    product_json,
    query_int,
    read_decimal,
    read_int,
    read_str,
    repayment_json,
    schedule_json,
)

api = Blueprint("api", __name__, url_prefix="/api")

MAX_PAGE_SIZE = 100


def db() -> Session:
    """One session per request. Committed or rolled back in the app's after_request hook."""
    if "db" not in g:
        g.db = current_app.extensions["loanlab.sessionmaker"]()
    return g.db


def service() -> LoanService:
    return LoanService(db(), current_app.extensions["loanlab.events"], current_app.extensions["loanlab.today"])


@api.get("/health")
def health():
    db().execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}


@api.get("/products")
def list_products():
    return jsonify([product_json(p) for p in service().products()])


@api.post("/loans/quote")
def quote():
    body = json_body()
    product, schedule = service().quote(
        read_str(body, "productCode", "Product code"),
        read_decimal(body, "amount", "Amount"),
        read_int(body, "months", "Months"),
    )
    return {"productCode": product.code, "annualRate": f"{product.annual_rate:.4f}", **schedule_json(schedule)}


@api.post("/loans")
@require_api_key
def open_loan():
    body = json_body()
    loan = service().open_loan(
        read_str(body, "customerName", "Customer name"),
        read_str(body, "productCode", "Product code"),
        read_decimal(body, "amount", "Amount"),
        read_int(body, "months", "Months"),
    )
    response = jsonify(loan_json(loan))
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_loan", loan_id=loan.id)
    return response


@api.get("/loans")
def list_loans():
    page = query_int("page", 1, 100_000)
    size = query_int("size", 20, MAX_PAGE_SIZE)
    loans, total = service().list_loans(request.args.get("status"), page, size)
    return {"items": [loan_json(loan) for loan in loans], "page": page, "size": size, "total": total}


@api.get("/loans/<int:loan_id>")
def get_loan(loan_id: int):
    return loan_json(service().get_loan(loan_id))


@api.get("/loans/<int:loan_id>/schedule")
def loan_schedule(loan_id: int):
    svc = service()
    loan = svc.get_loan(loan_id)
    return {"loanId": loan.id, "reference": loan.reference, **schedule_json(svc.schedule_for(loan))}


@api.get("/loans/<int:loan_id>/events")
def loan_events(loan_id: int):
    svc = service()
    return jsonify([event_json(e) for e in svc.history(svc.get_loan(loan_id))])


@api.post("/loans/<int:loan_id>/repayments")
@require_api_key
def repay(loan_id: int):
    body = json_body()
    repayment, created = service().repay(
        loan_id, read_decimal(body, "amount", "Amount"), request.headers.get("Idempotency-Key")
    )
    return repayment_json(repayment), 201 if created else 200


@api.get("/stats/portfolio")
def stats():
    return portfolio_stats(db())

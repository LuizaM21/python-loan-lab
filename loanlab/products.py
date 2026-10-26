"""The loan products. Names, rates and limits are fictional."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class LoanProduct:
    code: str
    name: str
    annual_rate: Decimal
    min_amount: Decimal
    max_amount: Decimal
    min_months: int
    max_months: int


_PRODUCTS = (
    LoanProduct("PERS", "Flexi Personal", Decimal("0.0990"), Decimal("1000.00"), Decimal("50000.00"), 6, 60),
    LoanProduct("AUTO", "Auto Plus", Decimal("0.0750"), Decimal("5000.00"), Decimal("150000.00"), 12, 84),
    LoanProduct("HOME", "Home Start", Decimal("0.0550"), Decimal("20000.00"), Decimal("500000.00"), 60, 360),
)

_BY_CODE = {product.code: product for product in _PRODUCTS}


def all_products() -> list[LoanProduct]:
    return list(_PRODUCTS)


def find_product(code: str | None) -> LoanProduct | None:
    return _BY_CODE.get((code or "").strip().upper())

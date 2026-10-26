"""Money helpers. All amounts are Decimal, never float."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def to_money(value: Decimal | int | str) -> Decimal:
    """Round to 0.01 with ROUND_HALF_UP (2.345 -> 2.35)."""
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def has_at_most_two_decimals(value: Decimal) -> bool:
    return value.is_finite() and value == value.quantize(CENT)


def format_money(value: Decimal) -> str:
    """ "10000" -> "10000.00". Used for every amount in JSON."""
    return f"{to_money(value):.2f}"

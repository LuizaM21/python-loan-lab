"""Kata: see the docstring. Run: pytest -m kata tests/katas/test_binary_search.py"""

from __future__ import annotations

from decimal import Decimal


def first_month_at_or_below(balances: list[Decimal], limit: Decimal) -> int | None:
    """`balances` is a repayment schedule's balance per month (index 0 = month 1), never increasing.
    Return the first MONTH NUMBER (1-based) whose balance is <= limit, or None.
    Target: O(log n). Do it by hand first; then compare with the bisect module."""
    raise NotImplementedError

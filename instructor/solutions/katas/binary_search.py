"""Reference solution."""

from __future__ import annotations

from decimal import Decimal


def first_month_at_or_below(balances: list[Decimal], limit: Decimal) -> int | None:
    """`balances` is a repayment schedule's balance per month (index 0 = month 1), never increasing.
    Return the first MONTH NUMBER (1-based) whose balance is <= limit, or None.
    Target: O(log n). Do it by hand first; then compare with the bisect module."""
    low, high = 0, len(balances)
    while low < high:
        mid = (low + high) // 2
        if balances[mid] <= limit:
            high = mid
        else:
            low = mid + 1
    return low + 1 if low < len(balances) else None

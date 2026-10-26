"""Reference solution."""

from __future__ import annotations


def best_streak(net_cashflow: list[int]) -> int:
    """The largest sum of a non-empty run of consecutive months (Kadane's algorithm, O(n)).
    best_streak([-2, 3, -1, 4, -10, 2]) -> 6   (3 - 1 + 4)
    Raise ValueError for an empty list."""
    if not net_cashflow:
        raise ValueError("no months")
    best = current = net_cashflow[0]
    for value in net_cashflow[1:]:
        current = max(value, current + value)
        best = max(best, current)
    return best

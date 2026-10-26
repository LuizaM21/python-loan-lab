"""Kata: see the docstring. Run: pytest -m kata tests/katas/test_coin_change.py"""

from __future__ import annotations


def fewest_notes(amount: int, notes: list[int]) -> int | None:
    """Fewest banknotes that add up exactly to `amount` (unlimited notes of each value), or None.
    Greedy is WRONG in general (amount 6 with notes [1, 3, 4]: greedy 4+1+1, best 3+3).
    Use dynamic programming: best[x] = 1 + min(best[x - note])."""
    raise NotImplementedError

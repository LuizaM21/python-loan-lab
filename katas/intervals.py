"""Kata: see the docstring. Run: pytest -m kata tests/katas/test_intervals.py"""

from __future__ import annotations


def merge_holidays(holidays: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Payment holidays as (first_month, last_month), inclusive, in any order.
    Merge overlapping or touching ones ((1, 3) and (4, 5) touch -> (1, 5)). Return them sorted."""
    raise NotImplementedError

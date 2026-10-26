"""Reference solution."""

from __future__ import annotations


def merge_holidays(holidays: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Payment holidays as (first_month, last_month), inclusive, in any order.
    Merge overlapping or touching ones ((1, 3) and (4, 5) touch -> (1, 5)). Return them sorted."""
    merged: list[tuple[int, int]] = []
    for start, end in sorted(holidays):
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged

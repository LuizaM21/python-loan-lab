"""Reference solution."""

from __future__ import annotations


def two_sum(amounts: list[int], target: int) -> tuple[int, int] | None:
    """Return the indexes (i, j), i < j, of two amounts that add up to target, or None.

    Use the first pair found when scanning left to right by j.
    two_sum([300, 150, 700, 50], 350) -> (0, 3)
    Target: O(n) time with a dict, not O(n^2).
    """
    seen: dict[int, int] = {}
    for j, amount in enumerate(amounts):
        i = seen.get(target - amount)
        if i is not None:
            return i, j
        seen.setdefault(amount, j)
    return None

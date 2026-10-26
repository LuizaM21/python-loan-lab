"""Reference solution."""

from __future__ import annotations


def fewest_notes(amount: int, notes: list[int]) -> int | None:
    """Fewest banknotes that add up exactly to `amount` (unlimited notes of each value), or None.
    Greedy is WRONG in general (amount 6 with notes [1, 3, 4]: greedy 4+1+1, best 3+3).
    Use dynamic programming: best[x] = 1 + min(best[x - note])."""
    if amount < 0:
        return None
    best: list[int | None] = [0] + [None] * amount
    for x in range(1, amount + 1):
        options = [best[x - n] for n in notes if n <= x and best[x - n] is not None]
        best[x] = min(options) + 1 if options else None
    return best[amount]

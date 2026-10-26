"""Kata: see the docstring. Run: pytest -m kata tests/katas/test_top_k.py"""

from __future__ import annotations


def top_customers(customer_names: list[str], k: int) -> list[str]:
    """The k names that appear most often, most frequent first; ties alphabetically.
    Hint: collections.Counter, then sorted with a key, or heapq.nsmallest."""
    raise NotImplementedError

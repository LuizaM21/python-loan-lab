"""Reference solution."""

from __future__ import annotations

from collections import Counter


def top_customers(customer_names: list[str], k: int) -> list[str]:
    """The k names that appear most often, most frequent first; ties alphabetically.
    Hint: collections.Counter, then sorted with a key, or heapq.nsmallest."""
    counts = Counter(customer_names)
    return [name for name, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:k]]

"""Kata: see the docstring. Run: pytest -m kata tests/katas/test_lru_cache.py"""

from __future__ import annotations


class LRUCache:
    """A cache that holds at most `capacity` keys and evicts the Least Recently Used one.
    get() and put() both count as a use. Both must be O(1).
    Do it without functools. Hint: collections.OrderedDict (move_to_end, popitem(last=False)).
    """

    def __init__(self, capacity: int) -> None:
        raise NotImplementedError

    def get(self, key: str) -> object | None:
        raise NotImplementedError

    def put(self, key: str, value: object) -> None:
        raise NotImplementedError

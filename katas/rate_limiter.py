"""Kata: see the docstring. Run: pytest -m kata tests/katas/test_rate_limiter.py"""

from __future__ import annotations

from collections.abc import Callable


class RateLimiter:
    """Allow at most `limit` calls per `window` seconds for each key (sliding window).
    `clock` returns the current time in seconds; tests pass a fake one. Never call time.time().
    allow(key) returns True and counts the call, or returns False and does not count it.
    """

    def __init__(self, limit: int, window: float, clock: Callable[[], float]) -> None:
        raise NotImplementedError

    def allow(self, key: str) -> bool:
        raise NotImplementedError

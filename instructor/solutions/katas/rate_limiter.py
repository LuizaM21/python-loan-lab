"""Reference solution."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable


class RateLimiter:
    def __init__(self, limit: int, window: float, clock: Callable[[], float]) -> None:
        self._limit, self._window, self._clock = limit, window, clock
        self._calls: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = self._clock()
        calls = self._calls[key]
        while calls and calls[0] <= now - self._window:
            calls.popleft()
        if len(calls) >= self._limit:
            return False
        calls.append(now)
        return True

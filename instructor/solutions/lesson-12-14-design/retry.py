"""Reference solution, lesson 13 task 2: retry as a FUNCTION decorator (copy to loanlab/retry.py)."""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from loanlab.credit import CreditBureauUnavailable

P = ParamSpec("P")
R = TypeVar("R")


def retry(
    attempts: int = 3,
    on: tuple[type[BaseException], ...] = (CreditBureauUnavailable,),
    base_delay: float = 0.2,
    sleep: Callable[[float], None] = time.sleep,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    def decorate(fn: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except on:
                    if attempt == attempts:
                        raise
                    sleep(base_delay * 2 ** (attempt - 1))
            raise AssertionError("unreachable")

        return wrapper

    return decorate

"""Lessons 14 and 15 exercise: a circuit breaker around the credit bureau (the State pattern).

Tests: tests/exercises/test_circuit_breaker.py   Run: pytest -m exercise tests/exercises/test_circuit_breaker.py

Why: when the bureau is down, every loan application waits for a timeout (2 s) times the retries.
Threads pile up, the API slows down for everyone. A breaker notices repeated failures and FAILS FAST
for a while, then carefully tries again.

CircuitBreakerBureau(inner, failure_threshold=3, reset_after=30.0, clock=time.monotonic)
is itself a CreditBureau (same `report()` method), so it can wrap anything and be wrapped by
anything (RetryingCreditBureau, MinCreditScore). Three states:

CLOSED (start)
- Calls go to `inner`. Success resets the failure count.
- CreditBureauUnavailable counts as a failure and is re-raised. At `failure_threshold` CONSECUTIVE
  failures the breaker goes OPEN and remembers clock() as the time it opened.
- CreditBureauRejected is NOT a failure: the bureau is up and answered. Re-raise, count unchanged.

OPEN
- Does not call `inner` at all. Raises CircuitOpen (a subclass of CreditBureauUnavailable, so
  MinCreditScore degrades to REFER without knowing about breakers).
- Once clock() - opened_at >= reset_after, the next call goes HALF_OPEN and is let through.

HALF_OPEN (one trial call)
- Success -> CLOSED, failure count 0.
- CreditBureauUnavailable -> OPEN again, with a new opened_at; re-raise.

`state` returns "closed", "open" or "half_open".

Pattern: implement each state as a small class with the same methods, and let the breaker delegate
to its current state object. Compare with one big if/elif on a string: which is easier to extend
with a fourth state?
"""

from __future__ import annotations

import time
from collections.abc import Callable

from loanlab.credit import CreditBureau, CreditBureauUnavailable, CreditReport


class CircuitOpen(CreditBureauUnavailable):
    pass


class CircuitBreakerBureau:
    def __init__(
        self,
        inner: CreditBureau,
        failure_threshold: int = 3,
        reset_after: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        raise NotImplementedError  # TODO lesson 14/15

    @property
    def state(self) -> str:
        raise NotImplementedError  # TODO lesson 14/15

    def report(self, customer_name: str) -> CreditReport:
        raise NotImplementedError  # TODO lesson 14/15

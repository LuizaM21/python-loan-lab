"""Reference solution, lessons 14/15: circuit breaker with the State pattern."""

from __future__ import annotations

import time
from collections.abc import Callable

from loanlab.credit import CreditBureau, CreditBureauUnavailable, CreditReport


class CircuitOpen(CreditBureauUnavailable):
    pass


class _State:
    name = "?"

    def __init__(self, breaker: CircuitBreakerBureau) -> None:
        self.breaker = breaker

    def report(self, customer_name: str) -> CreditReport:
        raise NotImplementedError


class _Closed(_State):
    name = "closed"

    def __init__(self, breaker: CircuitBreakerBureau) -> None:
        super().__init__(breaker)
        self.failures = 0

    def report(self, customer_name: str) -> CreditReport:
        try:
            result = self.breaker.inner.report(customer_name)
        except CreditBureauUnavailable:
            self.failures += 1
            if self.failures >= self.breaker.failure_threshold:
                self.breaker.transition(_Open(self.breaker))
            raise
        self.failures = 0
        return result


class _Open(_State):
    name = "open"

    def __init__(self, breaker: CircuitBreakerBureau) -> None:
        super().__init__(breaker)
        self.opened_at = breaker.clock()

    def report(self, customer_name: str) -> CreditReport:
        if self.breaker.clock() - self.opened_at >= self.breaker.reset_after:
            half_open = _HalfOpen(self.breaker)
            self.breaker.transition(half_open)
            return half_open.report(customer_name)
        raise CircuitOpen("Credit bureau circuit is open: failing fast.")


class _HalfOpen(_State):
    name = "half_open"

    def report(self, customer_name: str) -> CreditReport:
        try:
            result = self.breaker.inner.report(customer_name)
        except CreditBureauUnavailable:
            self.breaker.transition(_Open(self.breaker))
            raise
        self.breaker.transition(_Closed(self.breaker))
        return result


class CircuitBreakerBureau:
    def __init__(
        self,
        inner: CreditBureau,
        failure_threshold: int = 3,
        reset_after: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.inner = inner
        self.failure_threshold = failure_threshold
        self.reset_after = reset_after
        self.clock = clock
        self._state: _State = _Closed(self)
        # A real service shares one breaker between threads: guard transitions with a threading.Lock.

    @property
    def state(self) -> str:
        return self._state.name

    def transition(self, state: _State) -> None:
        self._state = state

    def report(self, customer_name: str) -> CreditReport:
        return self._state.report(customer_name)

"""Reference tests, lesson 13 task 2 (copy to tests/unit/test_retry.py; the code to loanlab/retry.py)."""

from __future__ import annotations

import pytest

from loanlab.credit import CreditBureauRejected, CreditBureauUnavailable
from loanlab.retry import retry  # type: ignore[import-not-found]


class TestRetry:
    def test_retries_then_returns_with_backoff(self):
        delays: list[float] = []
        outcomes = [CreditBureauUnavailable("1"), CreditBureauUnavailable("2"), "ok"]

        @retry(attempts=3, sleep=delays.append)
        def flaky() -> str:
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        assert flaky() == "ok"
        assert delays == [0.2, 0.4]

    def test_raises_after_the_last_attempt(self):
        calls: list[int] = []

        @retry(attempts=2, sleep=lambda s: None)
        def down() -> None:
            calls.append(1)
            raise CreditBureauUnavailable("down")

        with pytest.raises(CreditBureauUnavailable):
            down()
        assert len(calls) == 2

    def test_does_not_retry_other_errors(self):
        calls: list[int] = []

        @retry(sleep=lambda s: None)
        def rejected() -> None:
            calls.append(1)
            raise CreditBureauRejected("no")

        with pytest.raises(CreditBureauRejected):
            rejected()
        assert len(calls) == 1

    def test_keeps_the_function_name(self):
        @retry()
        def fetch_report() -> None: ...

        assert fetch_report.__name__ == "fetch_report"

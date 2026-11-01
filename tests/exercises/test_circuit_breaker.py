from decimal import Decimal
from unittest.mock import create_autospec

import pytest

from exercises.circuit_breaker import CircuitBreakerBureau, CircuitOpen
from loanlab.credit import CreditBureau, CreditBureauRejected, CreditBureauUnavailable, CreditReport

pytestmark = pytest.mark.exercise

REPORT = CreditReport("Ana Pop", 700, Decimal("0.00"))
DOWN = CreditBureauUnavailable("timeout")


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def inner():
    # autospec: the mock has exactly CreditBureau's methods and signatures. A typo fails the test.
    return create_autospec(CreditBureau, instance=True)


def breaker(inner, clock) -> CircuitBreakerBureau:
    return CircuitBreakerBureau(inner, failure_threshold=3, reset_after=30.0, clock=clock)


def fail_times(subject, times: int) -> None:
    for _ in range(times):
        with pytest.raises(CreditBureauUnavailable):
            subject.report("Ana Pop")


class TestClosed:
    def test_passes_calls_through(self, inner, clock):
        # setup

        inner.report.return_value = REPORT
        subject = breaker(inner, clock)

        # execute

        result = subject.report("Ana Pop")

        # verify

        assert result == REPORT
        inner.report.assert_called_once_with("Ana Pop")
        assert subject.state == "closed"

    def test_stays_closed_below_the_threshold(self, inner, clock):
        # setup

        inner.report.side_effect = DOWN
        subject = breaker(inner, clock)

        # execute

        fail_times(subject, 2)

        # verify

        assert subject.state == "closed"

    def test_a_success_resets_the_count(self, inner, clock):
        # setup

        inner.report.side_effect = [DOWN, DOWN, REPORT, DOWN, DOWN]
        subject = breaker(inner, clock)

        # execute

        fail_times(subject, 2)
        subject.report("Ana Pop")
        fail_times(subject, 2)

        # verify

        assert subject.state == "closed"

    def test_a_rejection_is_not_a_failure(self, inner, clock):
        # setup

        inner.report.side_effect = [DOWN, DOWN, CreditBureauRejected("no history"), DOWN]
        subject = breaker(inner, clock)

        # execute

        fail_times(subject, 2)
        with pytest.raises(CreditBureauRejected):
            subject.report("Ana Pop")

        # verify

        assert subject.state == "closed"
        fail_times(subject, 1)
        assert subject.state == "open"  # 3 consecutive Unavailable: the rejection did not reset


class TestOpen:
    def test_opens_at_the_threshold(self, inner, clock):
        # setup

        inner.report.side_effect = DOWN
        subject = breaker(inner, clock)

        # execute

        fail_times(subject, 3)

        # verify

        assert subject.state == "open"

    def test_fails_fast_without_calling_the_bureau(self, inner, clock):
        # setup

        inner.report.side_effect = DOWN
        subject = breaker(inner, clock)
        fail_times(subject, 3)
        inner.report.reset_mock()

        # execute

        clock.now += 29.9
        with pytest.raises(CircuitOpen):
            subject.report("Ana Pop")

        # verify

        inner.report.assert_not_called()

    def test_circuit_open_is_a_kind_of_unavailable(self):
        assert issubclass(CircuitOpen, CreditBureauUnavailable)


class TestHalfOpen:
    def test_lets_one_trial_through_after_the_wait_and_closes_on_success(self, inner, clock):
        # setup

        inner.report.side_effect = [DOWN, DOWN, DOWN, REPORT]
        subject = breaker(inner, clock)
        fail_times(subject, 3)

        # execute

        clock.now += 30.0
        result = subject.report("Ana Pop")

        # verify

        assert result == REPORT
        assert subject.state == "closed"

    def test_reopens_when_the_trial_fails_and_waits_again(self, inner, clock):
        # setup

        inner.report.side_effect = DOWN
        subject = breaker(inner, clock)
        fail_times(subject, 3)
        clock.now += 30.0

        # execute

        fail_times(subject, 1)

        # verify

        assert subject.state == "open"
        assert inner.report.call_count == 4
        clock.now += 29.0
        with pytest.raises(CircuitOpen):
            subject.report("Ana Pop")
        assert inner.report.call_count == 4  # still waiting: the wait restarted at the failed trial

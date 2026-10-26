import pytest

from katas.rate_limiter import RateLimiter

pytestmark = pytest.mark.kata


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_allows_up_to_the_limit_inside_the_window():
    clock = FakeClock()
    limiter = RateLimiter(limit=3, window=10, clock=clock)
    assert [limiter.allow("api-key-1") for _ in range(4)] == [True, True, True, False]


def test_window_slides():
    clock = FakeClock()
    limiter = RateLimiter(limit=2, window=10, clock=clock)
    assert limiter.allow("k")
    clock.now += 6
    assert limiter.allow("k")
    assert not limiter.allow("k")
    clock.now += 4  # the first call is now exactly 10 s old: it no longer counts
    assert limiter.allow("k")
    assert not limiter.allow("k")


def test_keys_are_independent_and_rejected_calls_do_not_count():
    clock = FakeClock()
    limiter = RateLimiter(limit=1, window=10, clock=clock)
    assert limiter.allow("a")
    assert not limiter.allow("a")
    assert limiter.allow("b")
    clock.now += 10
    assert limiter.allow("a")

from decimal import Decimal

import pytest

from katas.binary_search import first_month_at_or_below

pytestmark = pytest.mark.kata


BALANCES = [Decimal(v) for v in ["900", "800", "800", "500", "200", "0"]]


@pytest.mark.parametrize(
    ("limit", "expected"),
    [("1000", 1), ("900", 1), ("850", 2), ("800", 2), ("799.99", 4), ("0", 6), ("-1", None)],
)
def test_finds_the_first_month_at_or_below_the_limit(limit, expected):
    assert first_month_at_or_below(BALANCES, Decimal(limit)) == expected


def test_handles_an_empty_schedule():
    assert first_month_at_or_below([], Decimal("1")) is None

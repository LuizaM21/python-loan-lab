import pytest

from katas.intervals import merge_holidays

pytestmark = pytest.mark.kata


@pytest.mark.parametrize(
    ("holidays", "expected"),
    [
        ([], []),
        ([(2, 3)], [(2, 3)]),
        ([(5, 6), (1, 3)], [(1, 3), (5, 6)]),
        ([(1, 3), (2, 6)], [(1, 6)]),
        ([(1, 3), (4, 5)], [(1, 5)]),
        ([(1, 10), (2, 3)], [(1, 10)]),
        ([(8, 9), (1, 2), (3, 4), (6, 6)], [(1, 4), (6, 6), (8, 9)]),
    ],
)
def test_merges_overlapping_and_touching_holidays(holidays, expected):
    assert merge_holidays(holidays) == expected

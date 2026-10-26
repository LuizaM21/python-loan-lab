import pytest

from katas.max_subarray import best_streak

pytestmark = pytest.mark.kata


@pytest.mark.parametrize(
    ("values", "expected"),
    [([-2, 3, -1, 4, -10, 2], 6), ([5], 5), ([-3, -1, -2], -1), ([1, 2, 3], 6), ([4, -1, -1, 4], 6)],
)
def test_finds_the_best_run_of_consecutive_months(values, expected):
    assert best_streak(values) == expected


def test_rejects_an_empty_list():
    with pytest.raises(ValueError):
        best_streak([])

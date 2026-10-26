import pytest

from katas.two_sum import two_sum

pytestmark = pytest.mark.kata


@pytest.mark.parametrize(
    ("amounts", "target", "expected"),
    [
        ([300, 150, 700, 50], 350, (0, 3)),
        ([300, 150, 700, 50], 850, (1, 2)),
        ([5, 5], 10, (0, 1)),
        ([1, 2, 3], 100, None),
        ([], 0, None),
        ([-20, 30, 10], 10, (0, 1)),
    ],
)
def test_finds_two_amounts_that_add_up_to_the_target(amounts, target, expected):
    assert two_sum(amounts, target) == expected


def test_runs_in_linear_time():
    amounts = list(range(200_000))
    assert two_sum(amounts, 399_997) == (199_998, 199_999)

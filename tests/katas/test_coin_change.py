import pytest

from katas.coin_change import fewest_notes

pytestmark = pytest.mark.kata


@pytest.mark.parametrize(
    ("amount", "notes", "expected"),
    [
        (0, [1, 5], 0),
        (6, [1, 3, 4], 2),
        (11, [1, 5, 10], 2),
        (7, [2, 4], None),
        (300, [50, 100, 200], 2),
        (3, [], None),
    ],
)
def test_uses_the_fewest_notes(amount, notes, expected):
    assert fewest_notes(amount, notes) == expected

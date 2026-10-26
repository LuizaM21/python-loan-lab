import pytest

from katas.graph import transfer_path

pytestmark = pytest.mark.kata


TRANSFERS = [("A", "B"), ("B", "C"), ("C", "D"), ("A", "E"), ("E", "D"), ("D", "F"), ("X", "A")]


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        ("A", "D", ["A", "E", "D"]),
        ("A", "F", ["A", "E", "D", "F"]),
        ("A", "A", ["A"]),
        ("D", "A", None),
        ("X", "C", ["X", "A", "B", "C"]),
    ],
)
def test_finds_the_shortest_transfer_chain(source, target, expected):
    assert transfer_path(TRANSFERS, source, target) == expected


def test_handles_cycles():
    assert transfer_path([("A", "B"), ("B", "A"), ("B", "C")], "A", "C") == ["A", "B", "C"]

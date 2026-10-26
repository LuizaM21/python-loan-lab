import pytest

from katas.brackets import is_balanced

pytestmark = pytest.mark.kata


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", True),
        ("()", True),
        ("{[()()]}", True),
        ("f(x[0]) + {y}", True),
        ("(", False),
        (")(", False),
        ("([)]", False),
        ("((())", False),
        ("}", False),
    ],
)
def test_checks_bracket_pairs(text, expected):
    assert is_balanced(text) is expected

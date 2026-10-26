import pytest

from katas.top_k import top_customers

pytestmark = pytest.mark.kata


def test_returns_the_most_frequent_names_first():
    names = ["Ion", "Ana", "Ion", "Dan", "Ana", "Ion"]
    assert top_customers(names, 2) == ["Ion", "Ana"]


def test_breaks_ties_alphabetically():
    assert top_customers(["b", "a", "c", "a", "b", "c"], 2) == ["a", "b"]


def test_k_larger_than_the_number_of_names():
    assert top_customers(["x"], 5) == ["x"]
    assert top_customers([], 3) == []

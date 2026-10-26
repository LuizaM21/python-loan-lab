"""Kata: see the docstring. Run: pytest -m kata tests/katas/test_graph.py"""

from __future__ import annotations


def transfer_path(transfers: list[tuple[str, str]], source: str, target: str) -> list[str] | None:
    """`transfers` are directed edges (from_account, to_account).
    Return the SHORTEST chain of accounts from source to target (both included), or None.
    Ties: any shortest path is fine, but the tests use graphs with one shortest path.
    Hint: breadth-first search with collections.deque and a `previous` dict."""
    raise NotImplementedError

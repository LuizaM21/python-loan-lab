"""Reference solution."""

from __future__ import annotations

from collections import defaultdict, deque


def transfer_path(transfers: list[tuple[str, str]], source: str, target: str) -> list[str] | None:
    """`transfers` are directed edges (from_account, to_account).
    Return the SHORTEST chain of accounts from source to target (both included), or None.
    Ties: any shortest path is fine, but the tests use graphs with one shortest path.
    Hint: breadth-first search with collections.deque and a `previous` dict."""
    graph: dict[str, list[str]] = defaultdict(list)
    for a, b in transfers:
        graph[a].append(b)
    previous: dict[str, str | None] = {source: None}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        if node == target:
            path = []
            current: str | None = node
            while current is not None:
                path.append(current)
                current = previous[current]
            return path[::-1]
        for nxt in graph[node]:
            if nxt not in previous:
                previous[nxt] = node
                queue.append(nxt)
    return None

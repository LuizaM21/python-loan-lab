"""Loan event log: an append-only history of what happened to each loan.

The app uses InMemoryEventLog by default. Lesson 06 asks you to finish MongoEventLog;
the app switches to it when MONGO_URL is set.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import Any, Protocol


class EventLog(Protocol):
    def record(self, event_type: str, loan_reference: str, data: dict[str, Any]) -> None: ...

    def history(self, loan_reference: str) -> list[dict[str, Any]]: ...

    def counts_by_type(self) -> dict[str, int]: ...


def utcnow() -> datetime:
    # BSON dates have millisecond precision; keep the same here so both logs agree.
    now = datetime.now(UTC).replace(tzinfo=None)
    return now.replace(microsecond=now.microsecond // 1000 * 1000)


class InMemoryEventLog:
    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def record(self, event_type: str, loan_reference: str, data: dict[str, Any]) -> None:
        event = {"type": event_type, "loanReference": loan_reference, "at": utcnow(), "data": dict(data)}
        with self._lock:
            self._events.append(event)

    def history(self, loan_reference: str) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(e) for e in self._events if e["loanReference"] == loan_reference]

    def counts_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        with self._lock:
            for event in self._events:
                counts[event["type"]] = counts.get(event["type"], 0) + 1
        return counts


class MongoEventLog:
    """Lesson 06. `collection` is a pymongo Collection (or a mongomock one in tests).

    Store one document per event: {type, loanReference, at, data}.
    """

    def __init__(self, collection) -> None:
        self._collection = collection

    def ensure_indexes(self) -> None:
        """TODO lesson 06: a compound index that serves history(): loanReference, then at."""
        raise NotImplementedError

    def record(self, event_type: str, loan_reference: str, data: dict[str, Any]) -> None:
        """TODO lesson 06: insert one document. Don't let Mongo add `_id` to the caller's dict."""
        raise NotImplementedError

    def history(self, loan_reference: str) -> list[dict[str, Any]]:
        """TODO lesson 06: events for one loan, oldest first, without `_id`."""
        raise NotImplementedError

    def counts_by_type(self) -> dict[str, int]:
        """TODO lesson 06: {"loan_opened": 3, ...} with an aggregation pipeline ($group)."""
        raise NotImplementedError

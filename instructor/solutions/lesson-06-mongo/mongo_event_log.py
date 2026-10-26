"""Lesson 06 reference solution.

Replace the MongoEventLog class in loanlab/events.py with this one, and add
`from pymongo import ASCENDING` to that file's imports. `utcnow` already lives in events.py.
"""

from __future__ import annotations

from typing import Any

from pymongo import ASCENDING

from loanlab.events import utcnow  # only so this file imports on its own


class MongoEventLog:
    def __init__(self, collection) -> None:
        self._collection = collection

    def ensure_indexes(self) -> None:
        # equality field first, then the sort field: serves find({loanReference}).sort(at)
        self._collection.create_index([("loanReference", ASCENDING), ("at", ASCENDING)], name="loan_at")

    def record(self, event_type: str, loan_reference: str, data: dict[str, Any]) -> None:
        # a new dict: insert_one adds "_id" to the document it is given
        self._collection.insert_one(
            {"type": event_type, "loanReference": loan_reference, "at": utcnow(), "data": dict(data)}
        )

    def history(self, loan_reference: str) -> list[dict[str, Any]]:
        cursor = self._collection.find({"loanReference": loan_reference}, {"_id": 0}).sort(
            [("at", ASCENDING), ("_id", ASCENDING)]
        )
        return list(cursor)

    def counts_by_type(self) -> dict[str, int]:
        pipeline = [{"$group": {"_id": "$type", "count": {"$sum": 1}}}]
        return {row["_id"]: row["count"] for row in self._collection.aggregate(pipeline)}

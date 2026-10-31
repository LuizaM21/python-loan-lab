"""Reacting to loan events: the Observer pattern. Lesson 14.

The service already records events ("loan_opened", "repayment_recorded", "loan_closed") in an
EventLog. We want notifications without touching LoanService (open/closed principle), so:

    PublishingEventLog(inner_log, bus)   # Decorator: records as before, then publishes
    bus.subscribe("loan_closed", handler) # Observers: any number, added at wiring time

The service does not know who listens. Handlers do not know each other.

Production note: publishing in-process after `record()` can notify about a transaction that later
rolls back. Real systems use the OUTBOX pattern: write the event to an `outbox` table in the same
transaction, and a separate worker publishes it after commit (lesson 06).
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from .events import EventLog

logger = logging.getLogger("loanlab.notifications")

Event = dict[str, Any]
Handler = Callable[[Event], None]
ALL = "*"


class EventBus:
    """Subject: keeps the observers and tells them about each event."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, handler: Handler) -> Callable[[], None]:
        """Register a handler. `ALL` ("*") receives every event. Returns a function that unsubscribes."""
        with self._lock:
            self._handlers[event_type].append(handler)

        def unsubscribe() -> None:
            with self._lock:
                self._handlers[event_type].remove(handler)

        return unsubscribe

    def publish(self, event: Event) -> None:
        """Call every interested handler. One failing handler must not break the others,
        and must never break the business operation that produced the event."""
        with self._lock:
            handlers = [*self._handlers.get(event["type"], []), *self._handlers.get(ALL, [])]
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception("event handler failed", extra={"fields": {"eventType": event["type"]}})


class PublishingEventLog:
    """Decorator around any EventLog: same interface, and every recorded event is also published."""

    def __init__(self, inner: EventLog, bus: EventBus) -> None:
        self._inner = inner
        self._bus = bus

    def record(self, event_type: str, loan_reference: str, data: dict[str, Any]) -> None:
        self._inner.record(event_type, loan_reference, data)
        self._bus.publish({"type": event_type, "loanReference": loan_reference, "data": dict(data)})

    def history(self, loan_reference: str) -> list[dict[str, Any]]:
        return self._inner.history(loan_reference)

    def counts_by_type(self) -> dict[str, int]:
        return self._inner.counts_by_type()


# ----------------------------------------------------------------------------- a concrete observer


class Notifier(Protocol):
    def send(self, loan_reference: str, message: str) -> None: ...


@dataclass
class InMemoryNotifier:
    """A fake for tests and local runs. A real one would send e-mail or SMS (through a queue)."""

    sent: list[tuple[str, str]] = field(default_factory=list)  # never `= []`: shared by every instance

    def send(self, loan_reference: str, message: str) -> None:
        self.sent.append((loan_reference, message))


def loan_closed_handler(notifier: Notifier) -> Handler:
    """A closure: the returned function remembers `notifier`."""

    def handle(event: Event) -> None:
        notifier.send(event["loanReference"], f"Loan {event['loanReference']} is fully repaid. Thank you!")

    return handle

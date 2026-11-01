"""Reference tests for loanlab/notifications.py (lesson 14): Observer + Decorator, end to end with the service."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from loanlab.events import InMemoryEventLog
from loanlab.notifications import ALL, EventBus, InMemoryNotifier, PublishingEventLog, loan_closed_handler
from loanlab.services import LoanService


class TestEventBus:
    def test_delivers_to_subscribers_of_that_type_and_to_wildcards(self):
        bus = EventBus()
        seen: list[str] = []
        bus.subscribe("loan_closed", lambda e: seen.append("closed"))
        bus.subscribe(ALL, lambda e: seen.append("all"))
        bus.subscribe("loan_opened", lambda e: seen.append("opened"))

        bus.publish({"type": "loan_closed", "loanReference": "LN-0001", "data": {}})

        assert seen == ["closed", "all"]

    def test_a_failing_handler_does_not_stop_the_others(self, caplog):
        bus = EventBus()
        seen: list[str] = []

        def broken(event):
            raise RuntimeError("smtp down")

        bus.subscribe("loan_closed", broken)
        bus.subscribe("loan_closed", lambda e: seen.append("ok"))

        with caplog.at_level(logging.ERROR, logger="loanlab.notifications"):
            bus.publish({"type": "loan_closed", "loanReference": "LN-0001", "data": {}})

        assert seen == ["ok"]
        assert "event handler failed" in caplog.text

    def test_unsubscribe(self):
        bus = EventBus()
        seen: list[str] = []
        unsubscribe = bus.subscribe("x", lambda e: seen.append("x"))

        unsubscribe()
        bus.publish({"type": "x", "loanReference": "", "data": {}})

        assert seen == []


class TestPublishingEventLog:
    def test_notifies_when_a_loan_closes_without_changing_the_service(self, session):
        # setup: wiring only. LoanService is untouched (open/closed principle).

        bus = EventBus()
        notifier = InMemoryNotifier()
        bus.subscribe("loan_closed", loan_closed_handler(notifier))
        inner = InMemoryEventLog()
        service = LoanService(session, PublishingEventLog(inner, bus), today=lambda: date(2026, 3, 1))
        loan = service.open_loan("Ana Pop", "PERS", Decimal("1000.00"), 6)

        # execute

        service.repay(loan.id, Decimal("1000.00"), "close-it")

        # verify

        assert notifier.sent == [("LN-0001", "Loan LN-0001 is fully repaid. Thank you!")]
        assert [e["type"] for e in inner.history("LN-0001")] == ["loan_opened", "repayment_recorded", "loan_closed"]

    def test_each_notifier_has_its_own_list(self):
        assert InMemoryNotifier().sent is not InMemoryNotifier().sent

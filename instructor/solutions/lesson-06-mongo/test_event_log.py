"""Lesson 06 reference: ONE contract, run against every EventLog implementation.

Copy to tests/unit/test_event_log.py once MongoEventLog is finished.
"""

import pytest

from loanlab.events import InMemoryEventLog, MongoEventLog


def mongo_log():
    mongomock = pytest.importorskip("mongomock")
    log = MongoEventLog(mongomock.MongoClient()["loanlab"]["events"])
    log.ensure_indexes()
    return log


@pytest.fixture(params=["memory", "mongo"])
def log(request):
    return InMemoryEventLog() if request.param == "memory" else mongo_log()


class TestEventLogContract:
    def test_returns_one_loans_history_oldest_first(self, log):
        # setup

        log.record("loan_opened", "LN-0001", {"amount": "1000.00"})
        log.record("loan_opened", "LN-0002", {"amount": "5000.00"})
        log.record("repayment_recorded", "LN-0001", {"amount": "10.00"})

        # execute

        history = log.history("LN-0001")

        # verify

        assert [e["type"] for e in history] == ["loan_opened", "repayment_recorded"]
        assert history[0]["data"] == {"amount": "1000.00"}
        assert all("_id" not in e for e in history)

    def test_does_not_change_the_callers_data(self, log):
        # setup

        data = {"amount": "1.00"}

        # execute

        log.record("loan_opened", "LN-0009", data)

        # verify

        assert data == {"amount": "1.00"}

    def test_counts_events_by_type(self, log):
        # setup

        for reference in ["LN-1", "LN-2", "LN-3"]:
            log.record("loan_opened", reference, {})
        log.record("loan_closed", "LN-1", {})

        # execute

        counts = log.counts_by_type()

        # verify

        assert counts == {"loan_opened": 3, "loan_closed": 1}

    def test_unknown_loan_has_no_history(self, log):
        assert log.history("LN-404") == []


def test_mongo_index_serves_history():
    log = mongo_log()
    keys = [tuple(v["key"]) for v in log._collection.index_information().values()]
    assert (("loanReference", 1), ("at", 1)) in keys

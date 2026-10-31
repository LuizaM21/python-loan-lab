"""Reference solution, lesson 15: tests for loanlab/credit.py with test doubles.

Copy to tests/unit/test_credit.py. Every technique in the lesson appears once.
"""

from __future__ import annotations

import io
import json
import logging
import urllib.error
from decimal import Decimal
from unittest.mock import MagicMock, Mock, call, create_autospec, patch

import pytest

from loanlab.credit import (
    CreditBureau,
    CreditBureauRejected,
    CreditBureauUnavailable,
    CreditReport,
    HttpCreditBureau,
    RetryingCreditBureau,
    urllib_transport,
)

GOOD_BODY = json.dumps({"customerName": "Ana Pop", "score": 712, "activeDebt": "1200.50"})
REPORT = CreditReport("Ana Pop", 712, Decimal("1200.50"))


class TestHttpCreditBureau:
    def test_parses_a_good_answer(self):
        # setup: a Mock transport with a fixed return value (a stub)

        transport = Mock(return_value=(200, GOOD_BODY))
        bureau = HttpCreditBureau("https://bureau.example", transport=transport)

        # execute

        report = bureau.report("Ana Pop")

        # verify

        assert report == REPORT
        assert isinstance(report.active_debt, Decimal)

    def test_url_encodes_the_name_and_always_passes_a_timeout(self):
        # setup

        transport = Mock(return_value=(200, GOOD_BODY))
        bureau = HttpCreditBureau("https://bureau.example/", transport=transport, timeout=1.5)

        # execute

        bureau.report("Ana Pop & Co")

        # verify: the Mock recorded the call (a spy on the boundary)

        transport.assert_called_once_with("https://bureau.example/reports?name=Ana%20Pop%20%26%20Co", 1.5)

    @pytest.mark.parametrize("status", [429, 500, 502, 503])
    def test_server_side_problems_are_transient(self, status):
        bureau = HttpCreditBureau("https://b", transport=Mock(return_value=(status, "")))

        with pytest.raises(CreditBureauUnavailable):
            bureau.report("Ana Pop")

    @pytest.mark.parametrize("status", [400, 403, 404])
    def test_client_side_answers_are_permanent(self, status):
        bureau = HttpCreditBureau("https://b", transport=Mock(return_value=(status, "")))

        with pytest.raises(CreditBureauRejected):
            bureau.report("Ana Pop")

    @pytest.mark.parametrize(
        "body",
        [
            "not json",
            json.dumps({"score": 700}),
            json.dumps({"customerName": "A", "score": "high", "activeDebt": "0"}),
            json.dumps({"customerName": "A", "score": 900, "activeDebt": "0"}),
        ],
    )
    def test_a_broken_contract_is_permanent(self, body):
        bureau = HttpCreditBureau("https://b", transport=Mock(return_value=(200, body)))

        with pytest.raises(CreditBureauRejected):
            bureau.report("Ana Pop")

    def test_a_transport_exception_propagates_unchanged(self):
        # side_effect with an exception instance: the mock RAISES it
        transport = Mock(side_effect=CreditBureauUnavailable("timed out"))
        bureau = HttpCreditBureau("https://b", transport=transport)

        with pytest.raises(CreditBureauUnavailable, match="timed out"):
            bureau.report("Ana Pop")


class TestUrllibTransport:
    """The only code that touches the network. We patch urlopen where it is LOOKED UP."""

    def test_returns_status_and_body(self):
        response = MagicMock()  # MagicMock: supports `with ... as`, i.e. __enter__/__exit__
        response.__enter__.return_value.status = 200
        response.__enter__.return_value.read.return_value = b'{"ok": true}'

        with patch("loanlab.credit.urllib.request.urlopen", return_value=response) as urlopen:
            result = urllib_transport("https://b/x", 2.0)

        assert result == (200, '{"ok": true}')
        urlopen.assert_called_once_with("https://b/x", timeout=2.0)

    def test_http_errors_become_status_codes(self):
        error = urllib.error.HTTPError("https://b/x", 503, "down", {}, io.BytesIO(b"busy"))  # type: ignore[arg-type]

        with patch("loanlab.credit.urllib.request.urlopen", side_effect=error):
            assert urllib_transport("https://b/x", 2.0) == (503, "busy")

    @pytest.mark.parametrize("error", [urllib.error.URLError("no route"), TimeoutError("slow")])
    def test_network_failures_are_transient(self, error):
        with (
            patch("loanlab.credit.urllib.request.urlopen", side_effect=error),
            pytest.raises(CreditBureauUnavailable),
        ):
            urllib_transport("https://b/x", 2.0)


class TestRetryingCreditBureau:
    @pytest.fixture
    def inner(self):
        # autospec: only the real interface exists. inner.reprot(...) would fail loudly.
        return create_autospec(CreditBureau, instance=True)

    def test_returns_at_once_when_the_first_call_works(self, inner):
        inner.report.return_value = REPORT
        sleep = Mock()

        assert RetryingCreditBureau(inner, sleep=sleep).report("Ana Pop") == REPORT
        sleep.assert_not_called()

    def test_retries_transient_errors_with_exponential_backoff(self, inner):
        # setup: side_effect as a list -> one item per call; exceptions are raised, values returned

        inner.report.side_effect = [CreditBureauUnavailable("1"), CreditBureauUnavailable("2"), REPORT]
        sleep = Mock()
        bureau = RetryingCreditBureau(inner, attempts=3, base_delay=0.2, sleep=sleep)

        # execute

        result = bureau.report("Ana Pop")

        # verify

        assert result == REPORT
        assert inner.report.call_count == 3
        assert sleep.call_args_list == [call(0.2), call(0.4)]

    def test_gives_up_after_the_last_attempt_and_raises_the_last_error(self, inner):
        inner.report.side_effect = CreditBureauUnavailable("still down")
        sleep = Mock()

        with pytest.raises(CreditBureauUnavailable, match="still down"):
            RetryingCreditBureau(inner, attempts=3, sleep=sleep).report("Ana Pop")

        assert inner.report.call_count == 3
        assert sleep.call_count == 2  # no pointless wait after the last attempt

    def test_never_retries_a_permanent_answer(self, inner):
        inner.report.side_effect = CreditBureauRejected("no history")
        sleep = Mock()

        with pytest.raises(CreditBureauRejected):
            RetryingCreditBureau(inner, sleep=sleep).report("Ana Pop")

        inner.report.assert_called_once_with("Ana Pop")
        sleep.assert_not_called()

    def test_logs_each_retry(self, inner, caplog):
        inner.report.side_effect = [CreditBureauUnavailable("blip"), REPORT]

        with caplog.at_level(logging.WARNING, logger="loanlab.credit"):
            RetryingCreditBureau(inner, sleep=Mock()).report("Ana Pop")

        assert [r.getMessage() for r in caplog.records] == ["credit bureau unavailable, retrying"]
        assert caplog.records[0].fields["attempt"] == 1  # type: ignore[attr-defined]

    def test_rejects_zero_attempts(self, inner):
        with pytest.raises(ValueError):
            RetryingCreditBureau(inner, attempts=0)

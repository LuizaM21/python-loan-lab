"""Credit bureau client: the app's first EXTERNAL dependency (a fictional HTTP service).

Lessons 13-15 use this file:
- `CreditBureau` is a Protocol: the rest of the app depends on it, not on HTTP (DIP).
- `HttpCreditBureau` adapts an HTTP API to that Protocol (Adapter).
- `RetryingCreditBureau` wraps any CreditBureau and adds retries (Decorator).
- Everything slow or random is injected (transport, sleep), so tests need no network and no waiting.

The bureau API (fictional): GET {base_url}/reports?name=<customer name>
  200 {"customerName": "Ana Pop", "score": 712, "activeDebt": "1200.00"}
  404 no credit history          -> CreditBureauRejected (permanent: do not retry)
  429 / 5xx / timeout / no route -> CreditBureauUnavailable (transient: retry, then degrade)
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Protocol
from urllib.parse import quote

logger = logging.getLogger("loanlab.credit")

# (url, timeout in seconds) -> (HTTP status, body text)
Transport = Callable[[str, float], tuple[int, str]]


@dataclass(frozen=True, slots=True)
class CreditReport:
    customer_name: str
    score: int  # 300..850
    active_debt: Decimal


class CreditBureauError(Exception):
    """Anything that went wrong talking to the bureau."""


class CreditBureauUnavailable(CreditBureauError):
    """Transient: timeout, connection error, 429 or 5xx. Worth a retry."""


class CreditBureauRejected(CreditBureauError):
    """Permanent: the bureau answered, and the answer is no (4xx, bad data). A retry gives the same."""


class CreditBureau(Protocol):
    def report(self, customer_name: str) -> CreditReport: ...


def urllib_transport(url: str, timeout: float) -> tuple[int, str]:
    """The real network call. Tests never use it: they pass a fake or a Mock transport."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 (fixed scheme in config)
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:  # 4xx/5xx still carry a status code
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise CreditBureauUnavailable(f"Credit bureau not reachable: {exc}") from exc


class HttpCreditBureau:
    """Adapter: speaks HTTP + JSON on one side, returns CreditReport on the other."""

    def __init__(self, base_url: str, transport: Transport = urllib_transport, timeout: float = 2.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport
        self._timeout = timeout  # ALWAYS set a timeout: the default for sockets is "wait forever"

    def report(self, customer_name: str) -> CreditReport:
        url = f"{self._base_url}/reports?name={quote(customer_name)}"
        status, body = self._transport(url, self._timeout)
        if status == 429 or status >= 500:
            raise CreditBureauUnavailable(f"Credit bureau answered {status}.")
        if status == 404:
            raise CreditBureauRejected("No credit history for this customer.")
        if status != 200:
            raise CreditBureauRejected(f"Credit bureau answered {status}.")
        return self._parse(body)

    @staticmethod
    def _parse(body: str) -> CreditReport:
        try:
            data = json.loads(body, parse_float=Decimal)
            report = CreditReport(
                customer_name=str(data["customerName"]),
                score=int(data["score"]),
                active_debt=Decimal(str(data["activeDebt"])),
            )
        except (ValueError, KeyError, TypeError, InvalidOperation) as exc:
            # A contract break is not transient: retrying returns the same bad body.
            raise CreditBureauRejected(f"Credit bureau sent an unexpected body: {exc}") from exc
        if not 300 <= report.score <= 850:
            raise CreditBureauRejected(f"Credit score out of range: {report.score}.")
        return report


class RetryingCreditBureau:
    """Decorator: same interface as the bureau it wraps, plus retries with exponential backoff.

    Retries only CreditBureauUnavailable. Waits base_delay, 2*base_delay, 4*base_delay, ...
    In a real system add jitter (a random part of the delay) so many clients don't retry in sync.
    """

    def __init__(
        self,
        inner: CreditBureau,
        attempts: int = 3,
        base_delay: float = 0.2,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if attempts < 1:
            raise ValueError("attempts must be at least 1")
        self._inner = inner
        self._attempts = attempts
        self._base_delay = base_delay
        self._sleep = sleep

    def report(self, customer_name: str) -> CreditReport:
        for attempt in range(1, self._attempts + 1):
            try:
                return self._inner.report(customer_name)
            except CreditBureauUnavailable as exc:
                if attempt == self._attempts:
                    raise
                delay = self._base_delay * 2 ** (attempt - 1)
                logger.warning(
                    "credit bureau unavailable, retrying",
                    extra={"fields": {"attempt": attempt, "delaySeconds": delay, "error": str(exc)}},
                )
                self._sleep(delay)
        raise AssertionError("unreachable")  # the loop either returns or raises

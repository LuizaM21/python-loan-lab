# 15 — Mocks, and handling things in production

Time: 120 minutes.

Goal: test code that talks to the outside world with `unittest.mock` (correctly, not everywhere),
and explain how a backend survives slow, failing and flaky dependencies in production.

Lesson 02 introduced test doubles. This lesson goes deep on mocks, then uses them to test the
failure modes that production will throw at you.

## Learn: `unittest.mock` in depth

```python
from unittest.mock import Mock, MagicMock, call, create_autospec, patch

transport = Mock(return_value=(200, body))           # a stub: fixed answer
transport = Mock(side_effect=TimeoutError("slow"))    # raises when called
inner.report.side_effect = [DOWN, DOWN, REPORT]       # one item per call: raise, raise, return
transport = Mock(side_effect=lambda url, t: (200, body) if "Ana" in url else (404, ""))  # computed

transport.assert_called_once_with("https://b/reports?name=Ana%20Pop", 1.5)
sleep.call_args_list == [call(0.2), call(0.4)]
inner.report.call_count == 3
inner.report.assert_not_called()
```

| Tool | Use |
| --- | --- |
| `Mock()` | Any attribute or call returns another Mock. Flexible, and that is the danger. |
| `MagicMock()` | Also supports dunders: `with`, `len`, iteration. Needed to fake `urlopen(...)` used in `with`. |
| `return_value` | What a call returns. |
| `side_effect` | An exception (raised), an iterable (one per call), or a function (computes the result). |
| `create_autospec(CreditBureau, instance=True)` | Only the real methods, with the real signatures. `bureau.reprot()` fails instead of passing. |
| `Mock(spec=Thing)` | Same idea, attributes only (no signature checks). |
| `patch("pkg.module.name")` | Replace a name for the duration of a test (decorator or `with`). |
| `patch.object(obj, "attr")`, `patch.dict(os.environ, {...})` | Replace one attribute; set env vars temporarily. |
| pytest `monkeypatch` | `monkeypatch.setattr(...)`, `monkeypatch.setenv(...)`; undone after the test. |
| pytest `caplog` | Capture log records and assert on them. |

**Where to patch: where the name is LOOKED UP.** `credit.py` does `import urllib.request` and calls
`urllib.request.urlopen(...)`, so `patch("loanlab.credit.urllib.request.urlopen")` works. If a
module did `from urllib.request import urlopen`, it has its own name `urlopen`, and you must patch
`"that_module.urlopen"`; patching `urllib.request.urlopen` would not affect it.

**Mistakes that pass.** A plain `Mock` accepts any method name and any arguments. If the code under
test calls `bureau.reprot("Ana")` or `bureau.report("Ana", timeout=2)`, a plain Mock says nothing and
the test is green, while production crashes. With `create_autospec(CreditBureau, instance=True)`
the first raises `AttributeError` and the second `TypeError`. (Python 3.12+ already rejects misspelt
assertion names like `assert_called_once_wiht` or `called_once_with`; it cannot know your interface.)

### When to mock, when not to

| Situation | Use |
| --- | --- |
| Your own code (repositories, services, rules) | A **fake** (`FakeBureau`, `InMemoryEventLog`) or the real thing |
| The database | A **real** database: SQLite in memory here, PostgreSQL in a container for the real dialect. Mocking a Session tests nothing. |
| A remote service (HTTP, SMTP, payment) | Wrap it in **your own adapter** (`HttpCreditBureau`), mock the transport *below* it in the adapter's tests, and use a fake *above* it everywhere else |
| Time, randomness, sleep | **Inject** them (`today=`, `clock=`, `sleep=`). Patch only code you cannot change. |

"Don't mock what you don't own": if you mock `requests` all over your tests, your tests encode your
guesses about `requests`. Mock your adapter instead, and test the adapter against the real thing
(or a contract test) once.

Signs of over-mocking: the test repeats the implementation line by line; a refactoring that keeps
the behaviour breaks the tests; the test asserts calls but never a result.

## Learn: handling production

Production is where dependencies are slow, wrong, or gone. The code in `credit.py`, `eligibility.py`
and the breaker exercise is built for that. The checklist:

| Concern | Rule | In this repo |
| --- | --- | --- |
| **Timeouts** | Every network call has one. The default is often "wait forever". | `HttpCreditBureau(timeout=2.0)` |
| **Classify errors** | Transient (timeout, 429, 5xx) vs permanent (4xx, bad data). Only transient ones are retried. | `CreditBureauUnavailable` vs `CreditBureauRejected` |
| **Retries** | Few, with exponential backoff + **jitter**, only for **idempotent** operations, within a total time budget | `RetryingCreditBureau` |
| **Idempotency** | A retried write must not happen twice | `Idempotency-Key` on repayments |
| **Circuit breaker** | Stop calling a dependency that is down; fail fast; probe later | Exercise, lesson 14 |
| **Graceful degradation** | Without the bureau, don't approve and don't crash: refer to a human | `MinCreditScore` returns REFER |
| **Bulkheads** | Limit how much one dependency can take (threads, connections), so it can't sink the whole app | Separate pools, worker limits |
| **Errors at the boundary** | One handler turns domain errors into status codes; unexpected errors are logged with the stack and return a plain 500 (no stack traces to clients) | `create_app` error handlers |
| **Observability** | Structured logs with a request id; metrics (rate, errors, duration p95/p99); traces across services | JSON logs + `X-Request-ID` in `create_app` |
| **Health checks** | Liveness (process is alive) vs readiness (can serve: DB reachable). Don't make liveness depend on a remote service. | `GET /api/health`; `k8s/deployment.yaml` |
| **Configuration** | From the environment; secrets never in code or logs (12-factor) | `DEFAULTS` + env vars |
| **Safe releases** | Feature flags, canary, quick rollback; migrations that are backward compatible (expand, then contract) | Lesson 08, 04 |
| **Personal data** | Never log names, IDs, amounts per customer unless needed; mask them | (Ask: what do our logs contain?) |

### When it breaks anyway: incident handling

1. **Detect**: an alert on symptoms users feel (error rate, p95), not on every CPU spike.
2. **Mitigate first**: roll back, turn off the feature flag, scale up, open the breaker by hand.
   Restore service before you understand everything.
3. **Diagnose**: follow one request id through the logs; compare metrics before and after; what changed (deploy, config, traffic, a dependency)?
4. **Fix the root cause**, with a regression test that reproduces it (lesson 18).
5. **Blameless post-mortem**: timeline, impact, root cause, what made it worse, action items with owners.

## In this repo

| File | Shows |
| --- | --- |
| `loanlab/credit.py` | Timeouts, error classification, adapter, retries, injected `transport` and `sleep` |
| `tests/unit/test_credit.py` | One sample: a `Mock` transport as stub and spy |
| `loanlab/eligibility.py` | Graceful degradation (`REFER`) |
| `loanlab/notifications.py` | Handler failures isolated and logged |
| `loanlab/api/__init__.py` | Error handlers, JSON logs, request ids |

## Do

### 1. Test `credit.py` with mocks

In `tests/unit/test_credit.py`, add tests for:

1. 429 and every 5xx -> `CreditBureauUnavailable` (one `parametrize`).
2. 400, 403, 404 -> `CreditBureauRejected`.
3. Bad bodies: not JSON, a missing field, a non-number score, a score of 900 -> `CreditBureauRejected`.
4. The name is URL-encoded (`"Ana Pop & Co"`) and the timeout is always passed.
5. `urllib_transport` with `patch(...urlopen)`: a 200 (use a `MagicMock` for the `with` block), an
   `HTTPError` 503 becomes `(503, body)`, a `URLError` and a `TimeoutError` become `CreditBureauUnavailable`.
6. `RetryingCreditBureau` with `create_autospec(CreditBureau, instance=True)`: succeeds on the third
   try with sleeps `[0.2, 0.4]`; gives up after the last attempt **without** a last sleep; never
   retries `CreditBureauRejected`; logs one warning per retry (use `caplog`).

Then break the code on purpose (change `>= 500` to `> 500`) and check that a test fails.

### 2. Exercise: the circuit breaker

If you did not finish it in lesson 14: `pytest -m exercise tests/exercises/test_circuit_breaker.py`.
Notice the fake clock: the test controls time, nothing sleeps.

### 3. Incident drill

The eligibility endpoint (lesson 12 stretch) is live. At 09:14 the support team reports "the
whole app is slow". You get these log lines (shortened):

```json
{"ts": "09:13:58", "level": "INFO", "message": "request", "path": "/api/loans/eligibility", "status": 200, "durationMs": 214.0}
{"ts": "09:14:02", "level": "WARNING", "message": "credit bureau unavailable, retrying", "attempt": 1, "delaySeconds": 0.2, "error": "Credit bureau not reachable: timed out"}
{"ts": "09:14:04", "level": "WARNING", "message": "credit bureau unavailable, retrying", "attempt": 2, "delaySeconds": 0.4, "error": "Credit bureau not reachable: timed out"}
{"ts": "09:14:07", "level": "INFO", "message": "request", "path": "/api/loans/eligibility", "status": 200, "durationMs": 6634.0}
{"ts": "09:14:09", "level": "INFO", "message": "request", "path": "/api/loans", "status": 200, "durationMs": 5810.0}
{"ts": "09:14:15", "level": "ERROR", "message": "unhandled error", "exception": "sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached"}
{"ts": "09:14:30", "level": "INFO", "message": "request", "path": "/api/health", "status": 500, "durationMs": 30001.0}
```

In `notes/incident-drill.md` answer: (a) Where does 6,634 ms come from? Do the arithmetic.
(b) Why is `GET /api/loans`, which never calls the bureau, also slow? (c) Why does the health check
fail, and what will Kubernetes do next? Does that help? (d) What do you do in the next 10 minutes?
(e) Which three changes stop this from happening again? (f) Which test would have caught it?

### 4. Stretch: wire the real bureau

Add `CREDIT_BUREAU_URL` to `DEFAULTS` in `create_app`. When set, build
`CircuitBreakerBureau(RetryingCreditBureau(HttpCreditBureau(url, timeout=...)))`. Which wrapper goes
outside, the breaker or the retry, and why? (Think: does an open breaker count as one failure or three?)

## Check yourself

1. `Mock` vs `MagicMock` vs `create_autospec`. When do you need each?
2. `return_value` vs `side_effect`: three kinds of `side_effect`.
3. Where do you patch? Give the `from x import y` case.
4. Why not mock the database or `requests` directly? What do you do instead?
5. Which errors do you retry, and which never? Why must the operation be idempotent?
6. What is exponential backoff, and why add jitter?
7. Retry vs circuit breaker: what does each protect?
8. Liveness vs readiness probe: what goes in each?
9. Walk through how you handle a production incident.
10. Name three things you put in a log line, and one thing you never put there.

## Say it in the interview

- "I mock at the boundary: the HTTP transport under my own adapter. Above the adapter I use fakes.
  I use autospec so a mock can't drift from the real interface."
- "Every remote call has a timeout. I retry only transient errors, with backoff and jitter, and only
  idempotent operations. A circuit breaker stops us from queueing on a dead dependency, and when the
  bureau is down we degrade to manual review instead of failing the application."
- "In an incident I mitigate first, roll back or switch the flag, then diagnose by following a
  request id through the logs. Then a regression test, then a blameless post-mortem."

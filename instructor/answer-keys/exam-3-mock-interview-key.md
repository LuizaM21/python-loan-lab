# Exam 3 — Key

Score each answer 1–4:

| Score | Meaning |
| --- | --- |
| 4 | Clear, structured, correct, with a concrete example from this lab or work |
| 3 | Correct and clear, few examples |
| 2 | Partly correct, or vague |
| 1 | Wrong, or no answer |

Pass: average ≥ 3 and no 1 on questions 3, 4, 5, 6, 8, 9.

## What a 4 includes

**1. About yourself.** 60 seconds; QA and performance engineering background; Scala at Mambu;
the move to development is motivated and backed by real work (this repo); Endava fit.

**2. Scala to Python.** Dynamic typing, mutability by default, no compiler -> tests, mypy, ruff,
frozen dataclasses, pure functions; Decimal for money; pitfalls (mutable defaults, `is`).

**3. Repayments API.** `POST /loans/{id}/repayments` with API key and `Idempotency-Key`; 201 first
time, 200 for a retry, 409 for overpaying / closed / key reuse, 400 invalid, 404 unknown;
`GET` to list; money as strings; unique constraint on the key; row lock.

**4. Request flow.** URL -> Flask routing -> before_request (request id) -> decorator (API key)
-> view parses the body -> service validates rules and changes objects in the session -> flush
-> response -> after_request commits (or rolls back on error status) -> JSON log line ->
error handlers map exceptions to JSON.

**5. N+1.** Definition; detect with a query counter in tests (`assertNumQueries` in Django, an
engine event in SQLAlchemy), APM, or `echo`; fix with `selectinload`/`joinedload`,
`select_related`/`prefetch_related`, or an aggregate query.

**6. Concurrent repayments.** Lost update -> overpaying or wrong balance. `SELECT ... FOR UPDATE`
inside a short transaction, or optimistic version column with retry; idempotency key for retries;
test it under load on PostgreSQL (SQLite ignores `FOR UPDATE`).

**7. Flask or Django.** Any reasoned answer with trade-offs (team, admin needs, explicit
transactions, ecosystem, DRF vs FastAPI).

**8. Live coding: rate limiter.** A dict of deques per key; drop timestamps older than the window;
allow and record if under the limit; rejected calls are not recorded; O(1) amortized; clock
injected. Tests: up to the limit, the window sliding exactly at the edge, keys independent.
Reference: `instructor/solutions/katas/rate_limiter.py`. Give 4 only if they talk while coding
and mention tests.

**9. p95 regression.** Confirm with metrics (which endpoint, since which deploy); reproduce under
load; profile (py-spy, APM traces, query counts); compare with the previous release (git diff,
bisect); fix the biggest cost; measure again; add a guard (query-count test, k6 threshold in CI).
A story from their performance-engineering work earns the 4.

**10. GIL.** One thread runs bytecode at a time; released during I/O; threads for blocking I/O,
asyncio for many concurrent I/O with async libraries, processes for CPU-bound; gunicorn workers
and threads.

**11. Shipping.** Multi-stage slim non-root image, exec-form gunicorn, config from env, secrets
from a Secret store, readiness vs liveness, requests/limits from load tests, rolling updates,
migrations as a separate step, logs to stdout as JSON.

**12. AI agents.** Context file, small tasks, tests as oracle, see a test fail once, review every
line, CI, never secrets or real data; accountability stays with the developer.

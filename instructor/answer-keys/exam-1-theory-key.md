# Exam 1 — Key

## Part A (1 point each)

| Q | Answer | Q | Answer |
| --- | --- | --- | --- |
| 1 | b | 11 | d |
| 2 | c | 12 | b |
| 3 | a | 13 | c |
| 4 | d | 14 | a |
| 5 | c | 15 | b |
| 6 | a | 16 | d |
| 7 | b | 17 | a |
| 8 | d | 18 | c |
| 9 | a | 19 | b |
| 10 | c | 20 | d |

## Part B (2 points each)

Give 2 points for the key idea and a correct example; 1 point for the idea without precision.

**21.** `create_app(config)` builds and returns a new app with its own configuration and
dependencies. Tests can build an app with an in-memory database, a fixed clock and a fake event
log, without global state leaking between tests.

**22.** `flush` sends the pending SQL inside the open transaction; `commit` ends the transaction.
`open_loan` needs the database-generated `id` to build `LN-0001`, so it flushes to get the id,
sets the reference, and flushes again. The request still decides to commit or roll back.

**23.** Two transactions read the same value, both change it, the second write overwrites the
first. Pessimistic: lock the row (`SELECT ... FOR UPDATE`). Optimistic: a version column checked
in the `UPDATE ... WHERE version = ?`, retry on conflict.

**24.** The client sends `Idempotency-Key`. The server stores it with the repayment (unique
column). A retry with the same key and same loan and amount returns the stored repayment with
200 and charges nothing. The same key with a different amount or loan is 409, because it is a
different request reusing a key.

**25.** Real projects have green suites and bugs in what they don't test. A developer proves the
bug with a failing test at the lowest level, makes the smallest fix, and keeps the test as a
regression test.

**26.** Flask + SQLAlchemy: explicit control of layers and transactions; choose your own parts.
Django: ORM, migrations, admin, auth built in; DRF for APIs. For a lending API: either, with a
reason (e.g. Flask/FastAPI for a small focused service with explicit transactions; Django when
admin, auth and a quick back office matter). Any well-argued choice gets 2.

**27.** Write the event to an `outbox` table in the same database transaction as the change;
a separate process publishes outbox rows to the queue or log and marks them sent. Here, events
are recorded outside the transaction, so a failed commit could leave an event for something that
never happened (or the reverse).

**28.** (a) gunicorn worker processes, each with threads (I/O-bound requests). (b) processes
(`ProcessPoolExecutor`, or batch jobs), because it is CPU-bound and the GIL blocks threads.

**29.** Any four with reasons: pinned slim base (repeatable, small); dependencies before code
(layer cache); multi-stage (smaller, fewer CVEs); non-root user (limits damage); exec-form CMD
(signals, graceful shutdown); `PYTHONUNBUFFERED=1` (logs appear); healthcheck; no secrets in the
image; `.dockerignore`.

**30.** Any three: give context (`CLAUDE.md`, rules), small tasks; tests as the oracle, see new
tests fail once; read every line as a PR review; run linters/types/CI; no secrets or real data;
you stay accountable.

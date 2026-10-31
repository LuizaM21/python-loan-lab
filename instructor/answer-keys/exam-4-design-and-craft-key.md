# Exam 4 — Key

## Part A (1 point each)

| Q | Answer | Q | Answer |
| --- | --- | --- | --- |
| 1 | c | 11 | b |
| 2 | b | 12 | d |
| 3 | d | 13 | a |
| 4 | a | 14 | c |
| 5 | c | 15 | b |
| 6 | a | 16 | d |
| 7 | d | 17 | a |
| 8 | b | 18 | c |
| 9 | a | 19 | b |
| 10 | c | 20 | d |

Notes: 1 — `+=` on the list succeeds (in place), then the tuple item assignment fails. 2 — late
binding: each lambda reads `i` when called. 6 — "D" is also defensible as a second reason; the
question asks for the most direct one. 15 — one for the loans, one `IN (...)` for all repayments.

## Part B (2 points each)

Give 2 points for the key idea plus a correct example; 1 point for the idea without precision.

**21.** Assignment binds a name to an object; it never copies. Two names can share one mutable
object, and a function receives the caller's object.
```python
def add(tag, tags=[]):      # one list, created when the def runs, shared by every call
    tags.append(tag); return tags
def add(tag, tags=None):    # fix
    tags = [] if tags is None else tags; tags.append(tag); return tags
```

**22.**
```python
def log_calls(level=logging.INFO):
    def decorate(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            logger.log(level, "calling %s", fn.__name__)
            return fn(*args, **kwargs)
        return wrapper
    return decorate
```
Must have three levels and `functools.wraps`. 1 point if `wraps` is missing.

**23.** Composition = an object uses others passed in (`LoanService(session, events, today)`,
`RetryingCreditBureau(inner)`); flexible, swappable, testable. Inheritance for a true "is a" with a
shared contract and little behaviour in the base: the error hierarchy (`ValidationError(LoanLabError)`,
handled uniformly by the API). Mention of the fragile base class or class explosion earns full marks.

**24.** The rule (high level) depends on the `CreditBureau` Protocol, not on HTTP (low level); the
HTTP adapter also conforms to the Protocol and is plugged in by the composition root. Tests pass a
`FakeBureau` with a fixed score or error: no network, no `patch`.

**25.** Adapter converts one interface to another (`HttpCreditBureau`, `MongoEventLog`). Decorator
keeps the interface and adds behaviour around calls (`RetryingCreditBureau`, `PublishingEventLog`).
Facade gives one simple entry point to a subsystem (`LoanService`).

**26.** Inner: `create_autospec(CreditBureau, instance=True)` (or a fake) with `side_effect` lists.
`sleep`: a `Mock` (or a list's `append`), never the real `time.sleep`. Cases: (1) first call works ->
result returned, sleep not called; (2) fails twice then works -> 3 calls, sleeps `[0.2, 0.4]`;
(3) always unavailable -> raises after `attempts` calls, `attempts - 1` sleeps; (4) `CreditBureauRejected`
-> one call, no sleep, re-raised. Also acceptable: logs one warning per retry; `attempts=0` rejected.

**27.** Any four, each with its effect: a short timeout (bounded wait); fewer retries / a total time
budget (no 3x amplification); a circuit breaker (fail fast while it's down); graceful degradation to
REFER (applications still accepted); a bulkhead (separate worker/connection limits so other endpoints
keep capacity); async processing via a queue (the request returns at once); caching recent reports;
readiness probe that does not depend on the bureau (no restart storm); alerting on bureau latency.

**28.** One query loads N loans, then touching `loan.repayments` lazily runs one query per loan:
N + 1. Fixes: `selectinload(Loan.repayments)` (1 extra `IN` query), `joinedload` (a JOIN; better for
many-to-one), or aggregate in SQL (`func.sum` + `group_by`) when only totals are needed. Detect with a
query counter or `raiseload("*")` in tests.

**29.** Turning raw input into typed, consistent, trustworthy data and rejecting with a reason what
can't be trusted. Principles (any three, with a reason): read as text first; Decimal never float;
never drop silently, report line + every problem; ambiguity is an error; parsing in the cleaner,
rules in the service; keep the raw file; idempotent load; stream.

**30.** For example: "This 90-line file caused six tickets this month, two of them silent data loss
and one a limit breach. Every fix is slow because nothing is separated or tested, and the next format
change will cause another loss. In about two days, in small releasable steps protected by the tests
we just wrote, we route it through the same rules as the API and report every rejected row." First
steps: characterization tests (if not yet there); then `with open(..., encoding=...)` and
`read_file`/named fields instead of `row[0]`. Full marks need the business terms and a safe first step.

## Part C (oral) — what a 4 sounds like

1. LEGB; assignment makes a name local unless `nonlocal`/`global`; closures keep enclosing names.
2. Strips, `isdigit()`, `> 0`, raises `CleaningError`; tests include `"0"`, `"12.5"`, `""`, `None`, `" 12 "`.
3. api -> services -> domain (pure) and adapters (db, events, credit); imports point inward; `create_app` wires.
4. Problem first, then pattern: e.g. adapter for the bureau, decorator for retries, strategy for schedules.
5. Dict of lists; copy the handler list under a lock; try/except around each handler with logging.
6. Own adapter; mock the transport under it in the adapter's tests; fakes above it; contract test or
   sandbox against the real API; autospec.
7. Mitigate (rollback/flag/breaker) -> logs by request id, metrics before/after, what changed ->
   root cause -> regression test -> blameless post-mortem.
8. Query counter or `echo=True`; failing test with a query-count assertion; `selectinload`/aggregate.
9. Starts from the symptom, minimises to one row, sees it fail for the right reason.
10. Code that doesn't change, code being deleted, no tests and no time to add them, mid-incident.

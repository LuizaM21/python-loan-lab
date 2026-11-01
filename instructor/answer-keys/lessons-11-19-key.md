# Lessons 11–19 — Key for the tasks

Reference code and tests live in `instructor/solutions/`:

| Lesson | Solution |
| --- | --- |
| 11 | `exercises/money_value.py` |
| 12 | `exercises/eligibility_rules.py`; `lesson-12-14-design/test_eligibility.py` |
| 13 | `lesson-12-14-design/retry.py` + `test_retry.py` |
| 14 | `exercises/schedule_strategies.py`, `exercises/circuit_breaker.py`; `lesson-12-14-design/test_notifications.py` |
| 15 | `lesson-15-mocks/test_credit.py`; the circuit breaker above |
| 16 | `exercises/loan_repository.py` |
| 17 | `exercises/clean.py`; `lesson-17-import-export/test_extract_export.py`, `pandas_clean.py` |
| 18 | `lesson-18-bug-fixing/test_legacy_import.py` + `loan_import.py` (fixed) |
| 19 | `lesson-19-refactoring/pipeline.py`, `loan_import.py`, `test_pipeline.py` |

To check a solution: copy it over the stub (exercises go to `exercises/`, `clean.py` to
`loanlab/importer/clean.py`, tests to `tests/unit/`) and run `pytest -m "exercise or not kata"`.

## Lesson 11

**Task 1** (output on CPython 3.12):

| Line | Result | Why |
| --- | --- | --- |
| `t = (1, [2]); t[1] += [3]` | `TypeError`, and `t == (1, [2, 3])` | `+=` extends the list in place, then the tuple item assignment fails |
| `{1: "a", True: "b"}` | `{1: 'b'}` | `True == 1` and `hash(True) == hash(1)`: same key, first key kept, last value wins |
| lambdas in a comprehension | `[2, 2, 2]` | late binding: `i` is read when called |
| `sum(g), sum(g)` | `(5, 0)` | the generator is used up after one pass |
| `return` in `finally` | `"finally"` | `finally` overrides the `return` (and would swallow an exception) |
| `class A: tags = []` | `['x']` | class attribute shared by every instance |
| `sorted(["b", "a", "C"])`, with `key=str.lower` | `['C', 'a', 'b']`, `['a', 'b', 'C']` | upper case sorts before lower case by code point |
| `Decimal("1.10") == Decimal("1.1")`, hashes | `True, True` | equal values must hash equal |
| `[] is []`, `() is ()` | `False, True` | two new lists; CPython reuses the one empty tuple (an implementation detail: never rely on it; Python warns about `is` with a literal) |

**Task 3**: three nested functions for `@timed(threshold_ms=100)`: the factory takes the arguments,
returns the decorator, which takes the function and returns the wrapper.

## Lesson 12

**Task 1**: no layer imports upward. The domain modules (`schedule`, `money`, `products`,
`eligibility`) import nothing from `api` or `services`. `legacy/loan_import.py` reaches into the
private `_PRODUCTS`: a smell for lesson 19. If `schedule.py` imported `models.py`, move the shared
thing down into the domain (or pass values in), never import upward.

**Task 3** (`LoanReport`): SRP — it loads data, formats and sends mail (three reasons to change).
OCP — a new format means editing the `if/elif` (use a dict of formatter functions). DIP — it builds
its own engine from the environment and calls `smtplib` directly (inject a repository/session and a
`Mailer` Protocol). Also: `float` for money in JSON, no `with` for the session. Better shape:
`LoanReport(loans: Callable[[], Iterable[Row]], formatters: dict[str, Formatter], mailer: Mailer)`.

**Task 4** (stretch, design only): build the policy in `create_app` (or a small factory called
there) with `default_policy(bureau, count_active=...)`; the counting function closes over the
request's session (`lambda name: LoanRepository(db()).count_active_for(name)`); tests pass a
`FakeBureau`.

## Lesson 13

**Task 1**: Adapter — `HttpCreditBureau`, `MongoEventLog`. Object decorator — `RetryingCreditBureau`,
`PublishingEventLog`. Function decorator — `require_api_key`. Facade — `LoanService`. Composite —
`EligibilityPolicy`. Factory — `create_app`, `default_policy`, `_event_log`. Registry — `_BY_CODE`.
Null Object — `AllowAll`. Proxy — SQLAlchemy lazy-loaded `loan.repayments`.

**Task 3**: `an_application(**overrides)` is more Pythonic: keyword arguments with defaults already
are a builder. A fluent class pays off only for many optional parts or validation between steps.

**Task 4**: a Strategy passed as a plain callable (dependency injection of the clock). A `Clock`
class would add a named interface and room for more methods (`now()`, a test clock that advances).

## Lesson 14

**Task 3**: no change to `create_app` is needed for the test: `create_app(config,
events=PublishingEventLog(InMemoryEventLog(), bus))`. Outbox: the event is written to an outbox table
in the same transaction; a worker publishes after commit, so a rolled-back change never notifies.

**Task 4**: composition is easier to test (pass a fake loader) and can mix any reader with any
cleaner; Template Method needs a subclass per combination.

## Lesson 15

**Stretch (order of wrappers)**: `CircuitBreakerBureau(RetryingCreditBureau(HttpCreditBureau(...)))`.
The breaker outside counts one failure per *logical* call (after retries are exhausted), and when
open it skips the retries completely. With the retry outside, the retry would catch `CircuitOpen`
(it is a `CreditBureauUnavailable`) and retry a fast-fail three times with sleeps: pointless waiting.

**Incident drill**:

- (a) 3 attempts x 2.0 s timeout + 0.2 s + 0.4 s backoff = 6.6 s, i.e. ~6,634 ms.
- (b) Every worker thread is stuck waiting on the bureau, so other requests queue. Each stuck request
  also holds a pooled database connection while it waits (the session was opened earlier in the
  request), so the pool (5 + 10 overflow) runs out and even `GET /api/loans` waits, then fails.
- (c) `/api/health` needs a DB connection and waits 30 s for the pool. If liveness uses it, Kubernetes
  restarts the pods: in-flight requests are lost, the other pods get more load, cold starts: worse.
  Liveness should not depend on the DB or remote services; readiness may (it takes the pod out of the
  load balancer instead of killing it).
- (d) Mitigate: turn off the bureau check (feature flag -> every application REFER), or cut timeout
  and attempts via config and roll out; tell support; contact the bureau provider. Scaling up alone
  doesn't help: new pods block the same way.
- (e) A circuit breaker; a total time budget (one attempt with a short timeout at peak); don't hold
  a DB connection while calling a remote service (call the bureau before opening the transaction);
  a bulkhead (limit concurrent bureau calls); liveness probe without the DB; alert on bureau latency
  and error rate.
- (f) A unit test with a bureau fake that raises `CreditBureauUnavailable` after a delay, asserting
  REFER within the budget; and a k6 load test against a slow stub bureau checking that p95 of
  `GET /api/loans` stays within its threshold while eligibility is slow.

## Lesson 16

**Task 1** (verified): transient, `id` None -> pending, None -> persistent, 1 (after flush) ->
persistent after commit -> detached after close (with `expire_on_commit=False` the values are still
readable). Identity map: `get` and `select` return the same object (`is` is `True`). With
`expire_on_commit=True`: `DetachedInstanceError`. This repo builds JSON after the request's commit
and close, so it keeps values (`expire_on_commit=False`).

**Task 3**: without `selectinload`, `raiseload("*")` raises `InvalidRequestError` on `loan.repayments`.

**Task 4**: the atomic update is one round trip and cannot lose an update; but `repay()` still needs
the loan's status, reference and new balance for the events and the 409 messages, and the
idempotency check, so the row lock version keeps the code simpler here. Both are correct.

**Task 5**: `Application.objects.filter(status=Application.Status.SUBMITTED).values("product__code")
.annotate(total=Sum("amount")).order_by("product__code")`.

## Lesson 17

**Task 1** (expected counts):

Iași (`,`, English headers, 9 data rows + a blank line): imported 5 — lines 2, 3, 4, 5, 10.
Rejected 4 — line 6 `ana pop` (uniqueness: duplicate of line 2), 7 PERS 900,000 (business rule: max
50,000), 8 `CARD` (business rule: unknown product), 9 `2026-02-30` (validity). Problems that clean
fine: line 3 `auto` and `25,000.00`; line 4 extra spaces, `1,250.50`, `03/03/2026`; line 10 `18000.5`.

Cluj (BOM, `;`, Romanian headers, 5 rows): imported 2 — lines 2 and 3. Rejected 3 — line 4 no name
(completeness), 5 `twelve` months (validity; `120.000` reads as 120,000, which is fine for HOME),
6 `-500` (validity). Clean-able: `pers`, `10.000,50`, `04.03.2026`, `45000 RON`, `05/03/2026`.

**Task 3**: 1 query for any number of loans (the loop with `loan.repayments` would be 1 + 200).

**Task 4**: with pandas 3 and these files, mixed columns stay text, but Iași `months` becomes
`int64`, and the empty Cluj name becomes `NaN` (a float) so string methods and comparisons break on
it. A column whose values all look numeric becomes `float64`: try a one-column file
`amount\n10000.10\n0.1` and look at the values. Hence `dtype=str, keep_default_na=False`.

## Lesson 18

| Ticket | Root cause | Smallest fix |
| --- | --- | --- |
| IMP-105 | The importer builds `Loan` itself and never calls the service: no limit checks | Open loans through `LoanService.open_loan` |
| IMP-106 | `parse_date` returns `None` for an impossible date; the INSERT fails on NOT NULL; the bare `except` swallows it without `rollback()`, so the session is unusable for every later row | Treat an unparseable date as a row error; `session.rollback()` in the handler; record the error |
| IMP-101 | `replace(",", ".")` turns `1,250.50` into `1.250.50`; `float()` raises; `except: pass` drops the row silently | Parse with `parse_amount`; record every rejected row with its line number |
| IMP-102 | `%m/%d/%Y` is tried before `%d/%m/%Y` | Day-first formats only (`parse_date` from lesson 17) |
| IMP-104 | Duplicates compared on the raw name | Compare `customer_key(name)` |
| IMP-103 | `errors=[]` default list shared across calls in the long-running worker | `errors=None` + new list |

Interaction: with IMP-104 fixed, add a name to `seen` only after the row imported, or a failed row
would block a corrected later row for the same customer. Siblings for task 3: bare `except` in
`parse_date`; `open()` without `with`/encoding; `imported_count` global; `print` instead of logging;
`_PRODUCTS` private import; float maths for the payment.

## Lesson 19

See `solutions/lesson-19-refactoring/`. With it in place, all lesson 18 tests stay green unchanged,
and the `per-file-ignores` entry can be deleted: `ruff check .` and `mypy` pass.

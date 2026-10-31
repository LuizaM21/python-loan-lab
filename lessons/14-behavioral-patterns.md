# 14 — Behavioral patterns

Time: 90 minutes.

Goal: implement Strategy and State yourself, recognise Observer, Chain of Responsibility, Command,
Template Method and Iterator in this codebase, and choose between them.

Behavioral patterns are about **who does what, and who talks to whom**: how an algorithm is chosen,
how objects react to each other, how responsibility moves along.

## Learn: the patterns, with the problem first

| Pattern | Problem | Shape | In this repo |
| --- | --- | --- | --- |
| **Strategy** | Several ways to do one job; pick at run time | Same interface, interchangeable implementations | Schedule methods (exercise below) |
| **State** | Behaviour depends on a mode, and the mode changes | One object per state; the context delegates to the current one | Circuit breaker (exercise below) |
| **Observer** (publish/subscribe) | When X happens, others must react, and X must not know them | Subject keeps a list of handlers and calls them | `EventBus` in `notifications.py` |
| **Chain of Responsibility** | A request passes through handlers; each may handle, pass or stop it | A list of handlers, run in order | `EligibilityPolicy` (a REJECT stops the chain); Flask `before_request` hooks; WSGI middleware |
| **Command** | Treat a request as an object: queue it, log it, retry it, undo it | A data object + an executor | A repayment request + its `Idempotency-Key`; a Celery task |
| **Template Method** | Same skeleton, some steps vary | Base class with the skeleton, subclasses fill the hooks | `unittest.TestCase` (`setUp`, test, `tearDown`); contrast with the importer pipeline (lesson 19) |
| **Iterator** | Walk through items without knowing the storage | `__iter__`/`__next__`, or `yield` | `read_rows`, `loan_report_rows`, SQLAlchemy results |
| **Mediator** | Many objects talk to each other in a tangle | They all talk through one hub | The event bus acts as one between services |
| **Visitor** | Many operations over a fixed set of types | `functools.singledispatch`, or `match` on type | Turning each event type into a message |
| **Memento** | Save and restore an object's state | Snapshot object | A draft loan application, "undo" |
| **Specification** | Combine business rules with and/or/not | Rule objects with `&`, `|` | A richer version of the eligibility rules |

### Strategy vs State

Same class diagram, different intent. **Strategy**: the *caller* chooses the algorithm, and it does
not change by itself (the product decides "equal principal"). **State**: the *object* changes its
own state as events happen (the breaker opens after three failures, half-opens after 30 s).

### Strategy vs Template Method

Both vary part of an algorithm. Template Method uses **inheritance** (subclass overrides a step).
Strategy uses **composition** (pass the varying part in). Python code mostly prefers Strategy: it is
easier to test and to combine, and a strategy can be a plain function.

### Observer in production

In-process observers run in the same transaction and thread as the business call. A slow or failing
handler must not break the repayment, so `EventBus.publish` catches and logs handler errors. Worse:
if the transaction rolls back after publishing, the customer got a "fully repaid" e-mail for a
repayment that never happened. The production answer is the **outbox pattern**: write the event to
an `outbox` table in the same transaction, and a separate worker publishes it after commit, at
least once, so consumers must be idempotent.

### Chain of Responsibility, done carefully

Order matters: cheap and certain rules first, the remote call last. A REJECT stops the chain, so a
low income never costs a bureau call. A REFER does not stop it: the human reviewer wants every reason.

## In this repo

| File | Shows |
| --- | --- |
| `loanlab/notifications.py` | Observer: `EventBus`, handlers, unsubscribe, error isolation |
| `loanlab/eligibility.py` | Chain of Responsibility + Composite |
| `exercises/schedule_strategies.py` | Strategy + registry (your exercise) |
| `exercises/circuit_breaker.py` | State (your exercise) |
| `loanlab/importer/extract.py` | Iterator via generators |
| `loanlab/services.py` `repay()` | Command-like request with an idempotency key |

## Do

### 1. Exercise: Strategy for repayment schedules

Read `exercises/schedule_strategies.py`. First compute the 1,200.00 / 12% / 12 months example **by
hand** in your notes. Then make `pytest -m exercise tests/exercises/test_schedule_strategies.py`
green. Check: to add a third method ("interest only, balloon at the end"), what do you change?
It should be one new class and one registry line.

### 2. Exercise: State for the circuit breaker

Read `exercises/circuit_breaker.py` and make `tests/exercises/test_circuit_breaker.py` green. Write
it with **one class per state** (`_Closed`, `_Open`, `_HalfOpen`) that the breaker delegates to.
Then sketch the same thing as one class with `if self.state == "open": ... elif ...`. Which one would
you rather extend with a fourth state, for example "forced open" for maintenance?

### 3. Observer: wire notifications into the app

In `create_app`, wrap the event log: `PublishingEventLog(event_log, bus)`, and subscribe
`loan_closed_handler(InMemoryNotifier())`. Keep the notifier in `app.extensions` so a test can read
it. Write an API test: open a loan, repay it in full, and assert one message was "sent". Note that
`LoanService` did not change. Then explain the outbox problem in two sentences in your notes.

### 4. Template Method vs Strategy, on paper

Sketch the importer (lesson 19) as a Template Method:
`class BranchImporter(ABC)` with `run()` calling abstract `read()`, `clean()`, `load()`, and a
`IasiImporter` subclass. Then as composition: `LoanImporter(cleaner, loader).run(rows)`. Which is
easier to test? Which can mix the Cluj reader with the Iași cleaner without a new class?

## Check yourself

1. Strategy vs State: same structure, what is the difference?
2. Strategy vs Template Method: inheritance or composition? Which does Python code prefer, and why?
3. What can go wrong with in-process Observer when a transaction rolls back? What is the outbox pattern?
4. Why does a REJECT stop the eligibility chain but a REFER does not?
5. How does a generator implement the Iterator pattern?
6. Give a Command example from web backends. What does an idempotency key add to it?
7. What problem does a circuit breaker solve that retries alone make worse?

## Say it in the interview

- "Repayment schedules are a strategy: annuity or equal principal, chosen by name from a registry.
  A new method is a new class and one line, and each one is tested on its own."
- "The circuit breaker is the State pattern: closed, open, half-open, each a small class. It fails
  fast when the bureau is down, so we don't pile up threads waiting for timeouts."
- "Notifications are observers on an event bus, so the loan service doesn't know they exist. In
  production I'd publish through an outbox table so we never notify about a rolled-back transaction."

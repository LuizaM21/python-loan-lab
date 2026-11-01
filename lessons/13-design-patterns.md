# 13 — Design patterns in Python: creational and structural

Time: 75 minutes.

Goal: name the patterns in this codebase, say what problem each solves, and know when Python
makes a classic pattern unnecessary.

## Learn: what a pattern is (and isn't)

A design pattern is a **named, proven shape for a recurring problem**. The name is the value: "wrap
it in a decorator" says in four words what would take a paragraph. Patterns come from the "Gang of
Four" book (1994, C++ and Smalltalk), so some exist to work around missing language features.

Python already has first-class functions, duck typing, modules and decorators. So:

| Classic pattern | Often in Python just... |
| --- | --- |
| Strategy | a function passed as an argument (`key=str.lower`) |
| Singleton | a module (imported once), or `@functools.cache` on a factory function |
| Factory | a function, or a `dict` from name to class |
| Iterator | a generator |
| Command | a callable, or a dataclass + a function |
| Template Method | a function that takes the varying steps as arguments |

Use a class when the variant has state or several methods. Use a function when it doesn't.

Interview rule: never say "I used pattern X" without the problem: "the bureau is slow and flaky, so
I wrapped it in a decorator that adds retries, without changing the client".

## Learn: creational patterns (how objects get made)

| Pattern | Problem it solves | In this repo |
| --- | --- | --- |
| **Factory function / method** | Creating the object needs decisions or wiring the caller should not know | `create_app(config)`, `default_policy(bureau, count)`, `_event_log(mongo_url)` |
| **Registry** (factory by name) | Pick an implementation by a key from config or input | `_BY_CODE` in `products.py`; `strategy_for(name)` (lesson 14) |
| **Builder** | Build a complex object step by step, readably | `select(Loan).where(...).order_by(...).limit(...)` in SQLAlchemy; a test-data builder |
| **Singleton** | Exactly one instance | Avoid as a class. A module, or one instance made in the composition root and passed around |
| **Prototype** | Copy an existing object and change a little | `dataclasses.replace(product, annual_rate=Decimal("0.05"))` |
| **Abstract factory** | Families of related objects that must match | Rare in Python; e.g. "Postgres parts" vs "SQLite parts" |

Why seniors distrust Singletons: hidden global state, tests leak into each other, hard to swap for
a fake. "Only one" is a wiring decision for `create_app`, not a property of the class.

## Learn: structural patterns (how objects fit together)

| Pattern | Problem it solves | In this repo |
| --- | --- | --- |
| **Adapter** | You have an interface; the outside world speaks another | `HttpCreditBureau`: HTTP + JSON -> `CreditReport`. `MongoEventLog`: pymongo -> `EventLog` |
| **Decorator** (object) | Add behaviour to an object without changing it or subclassing it | `RetryingCreditBureau`, `PublishingEventLog`: same interface, wraps another |
| **Proxy** | Stand in for an object to control access to it | SQLAlchemy lazy relationships (`loan.repayments` loads on first access); a circuit breaker |
| **Facade** | One simple entry point over a subsystem | `LoanService`: hides session, events, schedule maths, locking |
| **Composite** | Treat a group like a single item | `EligibilityPolicy` is used like one rule but contains many |
| **Repository** (enterprise) | Collection-like access to stored objects, in domain language | Lesson 16's `LoanRepository` |
| **Unit of Work** (enterprise) | Track changes, write them in one transaction | The SQLAlchemy `Session` |

**Decorator pattern vs Python `@decorator`.** Same idea, different level. A Python decorator wraps a
*function* when it is defined (`@require_api_key`). The GoF Decorator wraps an *object* at run time
(`RetryingCreditBureau(bureau)`). Both keep the same interface and add behaviour around the call.

**Adapter vs Facade vs Decorator vs Proxy** (a favourite question): all wrap something.
Adapter *changes* the interface. Facade *simplifies* many things into one. Decorator *keeps* the
interface and *adds* behaviour. Proxy *keeps* the interface and *controls access* (lazy, cache,
permission, breaker).

## In this repo

| File | Patterns |
| --- | --- |
| `loanlab/credit.py` | Adapter, Decorator, Protocol as the target interface |
| `loanlab/notifications.py` | Decorator (`PublishingEventLog`) + Observer (lesson 14) |
| `loanlab/eligibility.py` | Composite, Factory function, Null Object |
| `loanlab/api/__init__.py` | Factory (`create_app`), composition root |
| `loanlab/products.py` | Registry (`_BY_CODE`) |
| `loanlab/services.py` | Facade |

## Do

### 1. Pattern hunt

For each, write the file, the class or function, and the **problem** it solves, in `notes/day-6.md`:
Adapter (two places), Decorator (object: two places; function: one place), Facade, Composite,
Factory (three places), Registry, Null Object, Proxy (one in SQLAlchemy).

### 2. A function decorator vs an object decorator

Write `retry(attempts=3, on=(CreditBureauUnavailable,), sleep=time.sleep)` as a **function**
decorator in `loanlab/retry.py`, with exponential backoff like `RetryingCreditBureau`. Test it with
a fake `sleep` that records the delays. Then answer: when is the function decorator better (any
function, no wrapper class)? When is the object decorator better (decide at run time what to wrap;
wrap an object from someone else; keep state across calls)?

### 3. A test-data builder

Applications in tests repeat five fields. Write `an_application(**overrides) -> Application` in
`tests/unit/builders.py` with sensible defaults, and use it in a test:
`an_application(amount=Decimal("15000.01"))`. Then write the same as a fluent class
(`ApplicationBuilder().amount("15000.01").build()`). Which is more Pythonic, and why?

### 4. Explain one choice

`LoanService` gets `today: Callable[[], date]` instead of a `Clock` class with a `today()` method.
Which pattern is that, and what would a class add?

## Check yourself

1. What is a design pattern? Why do some GoF patterns matter less in Python?
2. Adapter, Facade, Decorator, Proxy: one sentence each on the difference.
3. Why avoid a Singleton class? What do you do instead?
4. Name a Builder you use every day in SQLAlchemy (or in Gatling).
5. Python `@decorator` vs the Decorator pattern.
6. What is a Repository, and what is a Unit of Work? Which one is the SQLAlchemy Session?
7. Give an example of the Null Object pattern and the `if x is not None` checks it removes.

## Say it in the interview

- "The credit bureau client is an adapter: the domain sees a `CreditBureau` with one method, and
  HTTP stays at the edge. Retries are a decorator around it, so the client stays simple and I can
  test retries with a fake bureau."
- "In Python I reach for a function before a class. A strategy is often just a callable."
- "Coming from Gatling: the scenario DSL is a builder, feeders are iterators, and protocol config
  is a factory. I've used these patterns for years, now I name them."

# 12 — Composition, structure in code, and SOLID

Time: 90 minutes.

Goal: explain how this codebase is structured and why, apply each SOLID principle to real code,
and add a business rule without editing the code that runs the rules.

## Learn: composition over inheritance

| | Inheritance ("is a") | Composition ("has a") |
| --- | --- | --- |
| Example | `ValidationError(LoanLabError)` | `LoanService(session, events, today)` |
| Coupling | Subclass depends on the parent's internals; a parent change can break every child ("fragile base class") | Depends only on the interface of the part |
| Change at run time | No: fixed when the class is written | Yes: pass another part (a fake in tests, Mongo in prod) |
| Combinations | 3 behaviours x 3 variants = a class explosion | Combine small parts freely |

Use inheritance for a true "is a" with a shared contract (the error hierarchy: every error has a
`code` and a `status`, and the API handles them all the same way). Use composition for "uses a"
and for anything that varies: storage, clocks, remote services, rules.

```python
# Inheritance for behaviour: brittle
class RetryingHttpCreditBureau(HttpCreditBureau): ...
class CachedRetryingHttpCreditBureau(RetryingHttpCreditBureau): ...   # and so on

# Composition: each wrapper has the same interface and wraps any other
bureau = RetryingCreditBureau(HttpCreditBureau(url), attempts=3)
bureau = CircuitBreakerBureau(bureau)                                  # lesson 14
```

## Learn: structure in code

This repo is layered. Each layer only imports the layers **below** it:

```
api/ (Flask: HTTP in, JSON out)            routes.py, payloads.py, auth.py
  └─ services.py (use cases, rules, transactions boundary)
       ├─ schedule.py, money.py, products.py, eligibility.py   (pure domain: no I/O)
       └─ models.py, db.py (SQLAlchemy)     events.py, credit.py (outside world, behind Protocols)
create_app() = the composition root: the ONE place that builds the real parts and plugs them together
```

| Principle | What it buys you |
| --- | --- |
| Rules live in one place (the service) | One fix, everywhere. Lesson 18's importer bypassed it, and got bugs. |
| The domain core has no I/O | `schedule.py` tests run in microseconds; no database, no clock |
| Dependencies point inward, details plug in from outside | "Ports and adapters" / hexagonal: `CreditBureau` is the port, `HttpCreditBureau` the adapter |
| High cohesion, low coupling | A module changes for one reason; few modules know about each other |
| Constructor injection | Every dependency is visible in `__init__`; tests pass fakes, no patching |
| One composition root | Wiring is not spread across the code; easy to change for prod, test, local |

## Learn: SOLID with this repo

**S — Single responsibility.** A unit has one reason to change.
`payloads.py` changes when the JSON format changes; `services.py` when a rule changes. Each rule
in `eligibility.py` checks one thing. *Smell:* `loanlab/legacy/loan_import.py` reads CSV, parses,
validates, calculates, saves, commits and prints: seven reasons to change.

**O — Open/closed.** Open for extension, closed for modification. Add behaviour by adding code, not
by editing working code. `EligibilityPolicy` runs any list of rules: a new rule is a new class.
`PublishingEventLog` adds notifications without touching `LoanService`. *Smell:* a growing
`if product == "PERS": ... elif product == "AUTO": ...`.

**L — Liskov substitution.** A subtype must work wherever the base type is expected, with no
surprises: no stronger preconditions, no weaker results, no new exceptions. `InMemoryEventLog` and
`MongoEventLog` both satisfy `EventLog`, so the service works with either. `CircuitOpen` is a
`CreditBureauUnavailable`, so code that handles "unavailable" handles a tripped breaker too.
*Smell:* a subclass that raises `NotImplementedError` for a method of the parent; a `Square`
whose `set_width` also changes its height.

**I — Interface segregation.** Clients should not depend on methods they don't use. `MaxActiveLoans`
needs one question answered, so it takes one function (`count_active`), not a Session or a whole
repository. *Smell:* a "LoanManager" interface with 25 methods that every fake must implement.

**D — Dependency inversion.** High-level policy should not depend on low-level details; both depend
on an abstraction. `MinCreditScore` depends on the `CreditBureau` Protocol; HTTP is a detail plugged
in by `create_app`. *Smell:* `requests.get(...)` inside a business rule, which you can only test
with `patch`.

In Python, the "abstraction" is usually a `Protocol` (structural: no inheritance needed) or simply
a callable. Duck typing gives you DIP cheaply.

**Do not over-apply it.** SOLID is a tool for code that changes. A 20-line script does not need
three Protocols. YAGNI ("you aren't gonna need it") and KISS still apply: add the seam when the
second variant arrives, or when a test needs it.

## In this repo

| File | Shows |
| --- | --- |
| `loanlab/eligibility.py` | composition of rules; each SOLID letter is named in the docstring |
| `loanlab/services.py` | constructor injection (`session`, `events`, `today`) |
| `loanlab/api/__init__.py` | `create_app`, the composition root |
| `loanlab/errors.py` | inheritance used well: a small "is a" hierarchy |
| `loanlab/legacy/loan_import.py` | the counter-example: everything in one function |

## Do

### 1. Draw the dependency graph

Run `grep -rn "^from \.\|^from loanlab" loanlab/ | grep -v legacy` and draw who imports whom (boxes and
arrows, in `notes/day-6.md`). Check the rule: does any lower layer import a higher one? Which module
would you move if `schedule.py` started importing `models.py`?

### 2. Exercise: a new rule, without editing the policy

`exercises/eligibility_rules.py` has the rule from the risk team: a first-time customer may borrow
at most 15,000.00 RON without manual review. Make `tests/exercises/test_first_loan_cap.py` green.
The last test puts your rule into an `EligibilityPolicy` that you did not modify: that is the
open/closed principle, proven by a test. Commit: `feat: first loan cap eligibility rule`.

### 3. Spot the violations

What SOLID principles does this break? Write one sentence each and a better shape, in your notes.

```python
class LoanReport:
    def run(self, fmt: str, email: str) -> None:
        session = make_sessionmaker(make_engine(os.environ["DATABASE_URL"]))()
        loans = session.scalars(select(Loan)).all()
        if fmt == "csv":
            body = "\n".join(f"{l.reference},{l.outstanding}" for l in loans)
        elif fmt == "json":
            body = json.dumps([{"ref": l.reference, "out": float(l.outstanding)} for l in loans])
        else:
            raise ValueError(fmt)
        smtplib.SMTP("mail.bank.local").sendmail("noreply@bank", email, body)
```

### 4. Stretch: an eligibility endpoint

Design `POST /api/loans/eligibility` with body `{customerName, productCode, amount, months,
monthlyIncome}` that returns `{"outcome": "approve" | "refer" | "reject", "reasons": [...]}`. Where
does the policy get built (which file)? How does `MaxActiveLoans` count loans without the rule
knowing about SQLAlchemy? Which bureau do tests use? Build it test-first in a new blueprint file,
registered in `create_app`, if you have time.

## Check yourself

1. Composition vs inheritance: when is inheritance the right choice? Give an example from this repo.
2. Name the layers of this app and the rule about which way imports go.
3. What is a composition root? Where is it here?
4. Explain each SOLID letter in one sentence, each with an example from this repo.
5. How does a `Protocol` help with dependency inversion in Python?
6. When is applying SOLID a mistake?
7. Why does `MaxActiveLoans` take a function and not a Session?

## Say it in the interview

- "I prefer composition: small objects with one job, plugged together in one place. It keeps tests
  simple because every dependency comes in through the constructor."
- "In this project the business rules live in the service layer. The old importer bypassed it and
  imported loans outside the product limits; routing it through the service closed that whole
  class of bug, not just the one row someone reported."
- "Open/closed in practice: the eligibility policy runs a list of rules. A new rule from the risk
  team is a new class and a test. I didn't touch the code that already worked."

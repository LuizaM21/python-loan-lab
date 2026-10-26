# 02 — Tests and TDD as a developer

Time: 90 minutes.

Goal: write pytest tests the way a senior developer does, and build a feature test-first.

You already know test design from QA. This lesson is about the **developer's tools** and habits:
pytest, fixtures, fakes, TDD, and tests that keep refactoring safe.

## Learn: pytest

```python
import pytest
from decimal import Decimal


class TestLoanService:  # group related tests
    def test_opens_a_loan_that_appears_in_the_list(self, service):  # "service" is a fixture
        # setup

        amount = Decimal("10000.00")

        # execute

        service.open_loan("Ana Pop", "PERS", amount, 12)

        # verify

        loans, total = service.list_loans(status=None, page=1, size=20)
        assert total == 1  # plain assert; pytest shows both sides

    @pytest.mark.parametrize(("amount", "months"), [("1000.00", 6), ("50000.00", 60)])
    def test_accepts_the_limits(self, service, amount, months):  # one test, many inputs
        ...


def test_rejects_an_unknown_product(service):
    with pytest.raises(ValidationError) as error:  # expect an exception
        service.open_loan("Ana", "GOLD", Decimal("1000"), 12)
    assert error.value.message == "Unknown loan product."
```

| Feature | Use |
| --- | --- |
| Fixture (`@pytest.fixture`) | Setup you ask for by name. `yield` in it = teardown after the test. |
| `conftest.py` | Shared fixtures for a folder. See `tests/conftest.py`. |
| Fixture scope | `function` (default, fresh each test), `module`, `session`. The API `client` is `module`. |
| `parametrize` | Table-driven tests: boundaries and equivalence classes in one place. |
| `pytest.raises(..., match=...)` | Expect an error. |
| Markers | `-m kata`, `-m "not slow"`. |
| Useful flags | `-k name`, `-x` (stop at first failure), `--lf` (last failed), `-vv`, `--pdb` |
| Coverage | `pytest --cov=loanlab --cov-report=term-missing` |

Same idea as `// setup`, `// execute`, `// verify` in xUnit: **Arrange / Act / Assert**.

## Learn: test doubles in Python

| Double | In this repo |
| --- | --- |
| Fake | `InMemoryEventLog` (a list instead of MongoDB); SQLite in memory instead of PostgreSQL |
| Stub | `today=lambda: date(2026, 3, 1)`: a fixed clock |
| Mock | `unittest.mock.Mock()`; check calls with `mock.assert_called_once_with(...)` |
| Spy | `Mock(wraps=real_object)` |

Rules: prefer **fakes** over mocks for your own code (mocks test implementation details). Mock at
the **boundary** (an HTTP client, a payment gateway). With `unittest.mock.patch`, patch the name
where it is **looked up**, not where it is defined.

**Dependency injection** makes this easy: `LoanService(session, events, today)` gets its helpers
in the constructor. No global clock, no global database.

## Learn: TDD

1. **Red**: write one small failing test for the next bit of behaviour.
2. **Green**: the simplest code that passes.
3. **Refactor**: clean up with the tests green.

Why seniors use it: the tests describe behaviour, not implementation; you never have untested
code; refactoring is safe; and the design stays testable (small functions, injected dependencies).

Not dogma: for spikes and UI glue, test after. For money maths and business rules, test first.

## Learn: tests that keep refactoring safe

- Test **behaviour through the public interface** (`service.open_loan`), not private helpers.
- **Characterization test**: before changing legacy code you don't fully understand, pin its
  current output, then refactor. You will do this in lesson 07.
- A green test proves nothing until you have **seen it fail**: break the expected value once.
- **Mutation testing** (`mutmut`) changes the code and checks your tests notice. The hidden bugs
  in this lab are hand-made mutants.

## In this repo

| File | Shows |
| --- | --- |
| `tests/conftest.py` | `session`, `events`, `service` (fixed date) and `client` fixtures |
| `tests/unit/test_schedule.py` | a pure-function test |
| `tests/unit/test_loan_service.py` | a service test with a fresh in-memory database |
| `tests/api/test_loans_api.py` | an API test with the Flask test client |

## Do

All work goes in `tests/unit/`. Run `pytest` after each test.

### 1. Boundaries for the products

In `test_loan_service.py`, one `parametrize` test that **accepts** every product limit
(min/max amount, min/max months for PERS, AUTO and HOME), and one that **rejects** one cent or
one month outside each limit, with the exact message. Check that rejected loans are not saved.

### 2. Customer names

`None`, `""`, `"   "` -> `"Customer name is required."`; 101 characters -> rejected; exactly 100
-> accepted; `"  Ion  "` is saved as `"Ion"`.

### 3. Repayments

Partial repayment reduces `outstanding`. Paying exactly the outstanding amount closes the loan.
One cent more is a `Conflict`. A closed loan rejects any repayment. The same `Idempotency-Key`
twice charges once; the same key with a different amount is a `Conflict`.

### 4. A fixed clock

Build a `LoanService` with `today=lambda: date(2026, 8, 15)` and check `created_on`.

### 5. Feature, test-first: totals on the quote

The product owner asks: "Show the total paid and the total interest on the quote."

1. Red: in `test_schedule.py`, test that 10,000.00 PERS over 12 months has `total_paid == 10544.33`
   and `total_interest == 544.33`. Work out why by hand (11 × 878.69 + 878.74). Run: it fails.
2. Green: add `total_paid` and `total_interest` to `Schedule` (a `@property` is fine).
3. Red/green again at the API level: `POST /api/loans/quote` returns `"totalPaid"` and
   `"totalInterest"` as strings with 2 decimals.
4. Refactor. Commit: `feat: totals on the loan quote`.

### 6. Red/green and coverage

Break one expected value. See the failure message. Put it back. Then run
`pytest --cov=loanlab --cov-report=term-missing` and find one untested line worth a test.

## Check yourself

1. What is a fixture, and how is it different from a `setUp` method?
2. Why is the API `client` fixture `module`-scoped, and what rule does that force on your tests?
3. Fake vs mock: which do you prefer for your own code, and why?
4. Where do you `patch` a function: where it is defined or where it is used?
5. Describe red-green-refactor. When would you not do TDD?
6. 100% line coverage, and a bug still gets through. How?
7. What is a characterization test?

## Say it in the interview

- "I write the test from the rule, not from the code. For a 1,000–50,000 limit I test 999.99,
  1,000.00, 50,000.00 and 50,000.01."
- "I prefer fakes for my own code and mocks only at system boundaries, so tests don't break
  when I refactor."
- "I came from QA, so I review test cases as a developer would want them: boundaries, negative
  paths, side effects, isolation and readable names."

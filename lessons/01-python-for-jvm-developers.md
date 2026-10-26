# 01 — Python for a JVM developer

Time: 75 minutes.

Goal: read and write the Python in this repo with confidence, and know where Python differs
from Scala and Java.

## Learn: the toolchain

| Task | Python | JVM equivalent |
| --- | --- | --- |
| Isolated dependencies | `python -m venv .venv`, then activate | one classpath per sbt/Maven project |
| Install dependencies | `pip install -r requirements-dev.txt` | `sbt update`, `mvn install` |
| Project config | `pyproject.toml` | `build.sbt`, `pom.xml` |
| Run tests | `pytest` | `sbt test` |
| Lint and format | `ruff check .`, `ruff format .` | scalafmt / scalafix |
| Type check | `mypy` (hints are not checked at runtime) | the compiler |
| REPL | `python`, or `python -i file.py` | `sbt console` |

A **package** is a folder with `__init__.py` (`loanlab/`). A **module** is one `.py` file
(`loanlab/schedule.py`). `from .money import to_money` is a relative import inside the package.

## Learn: just enough Python

```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)  # like a Scala case class: value equality, immutable
class LoanProduct:
    code: str
    annual_rate: Decimal  # type hints: documentation + mypy, not runtime checks


def monthly_payment(amount: Decimal, annual_rate: Decimal, months: int) -> Decimal:
    if months < 1:
        raise ValueError("months must be at least 1")  # exceptions, not Either/Try
    r = annual_rate / 12
    return to_money(amount * r / (1 - (1 + r) ** -months))
```

| Item | Meaning |
| --- | --- |
| `Decimal("0.1")` | Exact decimal. Build it from a **string** or an int. `Decimal(0.1)` copies the float error. |
| `0.1 + 0.2` | `0.30000000000000004`. Never use `float` for money. |
| `x: str \| None` | The value can be `None` (Scala `Option[String]`). Check with `if x is None`. |
| `[f(x) for x in xs if p(x)]` | List comprehension: `xs.filter(p).map(f)`. |
| `(f(x) for x in xs)` | Generator: lazy, like an `Iterator`. |
| `with open(path) as f:` | Context manager: closes the file even on error (`Using` in Scala). |
| `@functools.wraps` decorator | A function that wraps a function. `@require_api_key` in this repo. |
| `typing.Protocol` | A structural interface: any class with the right methods fits (`EventLog`). |
| `is` vs `==` | Identity vs equality. Use `is` only for `None`, `True`, `False`. |
| `def f(xs=[])` | **Bug**: the default list is created once and shared by every call. Use `None`. |
| `*args, **kwargs` | Any positional / keyword arguments. |
| f-string | `f"LN-{loan_id:04d}"` -> `LN-0007`. `f"{amount:.2f}"` -> `10.50`. |

Scala to Python, quickly: `xs.map(f)` -> `[f(x) for x in xs]`; `xs.groupBy(f)` -> a loop with
`dict.setdefault(k, []).append(x)`; `xs.foldLeft(0)(_ + _)` -> `sum(xs)`; `copy(a = 1)` ->
`dataclasses.replace(obj, a=1)`; `sealed trait` -> `enum.Enum`; `match` exists since 3.10.

## Learn: what Python does NOT do for you

- **No compiler.** A typo in a rarely used branch only fails when that line runs. Tests and
  `mypy` are your compiler.
- **Mutable by default.** Lists and dicts are shared by reference. Prefer tuples and
  `frozen=True` dataclasses for values.
- **Duck typing.** Any object with the right methods works. `Protocol` documents the contract.
- **One thread at a time for Python code (the GIL).** Lesson 07.

## In this repo

| File | Shows |
| --- | --- |
| `loanlab/money.py` | `Decimal`, `quantize`, `ROUND_HALF_UP` |
| `loanlab/products.py` | frozen dataclass, a module-level dict as a lookup table |
| `loanlab/schedule.py` | pure functions, a `tuple` of dataclasses, the loan maths |
| `loanlab/events.py` | `Protocol`, a lock for thread safety, a class with `NotImplementedError` stubs |
| `loanlab/api/auth.py` | a decorator with `functools.wraps`, `hmac.compare_digest` |
| `katas/` | stubs for interview exercises |

## Do

### 1. Set up and explore

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest
python
>>> from decimal import Decimal
>>> 0.1 + 0.2, Decimal("0.1") + Decimal("0.2"), Decimal(0.1)
>>> from loanlab import schedule
>>> s = schedule.calculate(Decimal("20000"), Decimal("0.099"), 24)
>>> s.monthly_payment, s.instalments[0], s.instalments[-1]
```

### 2. The maths by hand

Maria Ionescu's loan (LN-0001): 20,000.00 RON, Flexi Personal at 9.90%, 24 months.

Work out on paper: the monthly rate; month 1 interest (balance × rate, rounded half-up); month 1
principal; the balance after month 1. Then check against `GET /api/loans/1/schedule`.
(Monthly payment: 921.98.)

### 3. Read the code like a reviewer

Read `loanlab/schedule.py` and `loanlab/services.py`. In `notes/day-1.md`, write:

- Where can each `ValidationError` in `services.py` come from? List them all.
- Why does the last instalment have its own branch?
- Which functions are pure (no database, no clock)? Why does that matter for tests?

### 4. Tools

```bash
ruff check .            # lint
ruff format --check .   # formatting
mypy                    # types, configured in pyproject.toml
```

Break a type on purpose (`months: int` -> pass `"12"` somewhere) and see what `mypy` says, and
what happens at runtime. Put it back.

### 5. Katas

`two_sum` and `brackets` from `katas/`. Run `pytest -m kata tests/katas/test_two_sum.py`.
Say the complexity out loud before you write code.

## Check yourself

1. Why must money be `Decimal`, built from a string?
2. What does `frozen=True` give you, and what does it cost?
3. What is the bug in `def add(item, items=[])`? How do you fix it?
4. List comprehension vs generator expression: when is each evaluated, and what about memory?
5. What does a decorator do? What breaks without `functools.wraps`?
6. `is` vs `==`: when is `is` the right choice?
7. Type hints are not checked at runtime. How do you still get value from them?

## Say it in the interview

- "My main language is Scala, so I think in immutable data and pure functions. In Python I get
  that with frozen dataclasses, tuples and functions without side effects, and I lean on mypy
  and tests because there is no compiler."
- "For money I use `Decimal` built from strings, with explicit rounding. Never floats."
- "I keep the maths pure and push I/O to the edges, so most of the logic is tested in milliseconds."

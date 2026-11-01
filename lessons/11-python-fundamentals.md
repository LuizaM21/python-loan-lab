# 11 — Python fundamentals, the deep version

Time: 90 minutes.

Goal: answer "how does Python actually work?" questions without hesitating, and write a class
that behaves like a built-in type.

Lesson 01 got you reading the code. This lesson is the layer under it: objects, names, the data
model, and the traps interviewers like.

## Learn: names and objects

Everything is an object. A variable is a **name bound to an object**, not a box that holds a value.

```python
a = [1, 2]
b = a            # a second name for the SAME list
b.append(3)
a                # [1, 2, 3]
b = [9]          # rebinds b only; a is unchanged
```

| Idea | Meaning |
| --- | --- |
| Mutable | `list`, `dict`, `set`, most objects. Changing it changes it for every name bound to it. |
| Immutable | `int`, `str`, `tuple`, `frozenset`, `Decimal`, frozen dataclasses. "Changing" makes a new object. |
| Passing arguments | "Pass by object reference": the function gets the same object. Mutating it is visible to the caller; rebinding the parameter is not. |
| `is` vs `==` | Same object vs equal value. `is` only for `None`, `True`, `False`. |
| `copy.copy` / `copy.deepcopy` | Shallow copy (new outer object, same inner objects) / full copy. |
| Hashable | Has a `__hash__` that never changes, and `==` objects have equal hashes. Required for `dict` keys and `set` items. Mutable built-ins are not hashable. |

Scope is **LEGB**: Local, Enclosing function, Global (module), Built-in. Assigning to a name makes it
local to that function, unless you declare `nonlocal` (enclosing) or `global`.

## Learn: the data model (dunder methods)

Python syntax calls special methods. Write them and your class works with the syntax.

| You write | Python calls | Notes |
| --- | --- | --- |
| `repr(x)`, `str(x)` | `__repr__`, `__str__` | `repr` for developers (unambiguous), `str` for users |
| `x == y`, `x < y` | `__eq__`, `__lt__` | Return `NotImplemented` for types you don't handle: Python then tries the other side |
| `hash(x)` | `__hash__` | Define `__eq__` without `__hash__` and instances become unhashable |
| `x + y`, `0 + x` | `__add__`, `__radd__` | `__radd__` is why `sum()` (which starts at 0) can work |
| `bool(x)`, `if x:` | `__bool__` (or `__len__`) | |
| `len(x)`, `x[i]`, `k in x` | `__len__`, `__getitem__`, `__contains__` | the container protocol |
| `for v in x` | `__iter__` (and `__next__` on the iterator) | the iteration protocol |
| `with x as y` | `__enter__`, `__exit__` | the context manager protocol |
| `x()` | `__call__` | objects that act like functions |
| `x.attr = v` | `__setattr__` | how to make something immutable |

`@functools.total_ordering`: write `__eq__` and `__lt__`, get `<=`, `>`, `>=` for free.
`__slots__ = ("a", "b")`: no per-instance `__dict__`. Less memory, and no new attributes by typo.

## Learn: functions are objects

```python
def retry(attempts: int):                       # a decorator WITH arguments: three levels
    def decorate(fn):
        @functools.wraps(fn)                    # keep fn's name and docstring
        def wrapper(*args, **kwargs):
            for attempt in range(1, attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except TimeoutError:
                    if attempt == attempts:
                        raise
        return wrapper
    return decorate
```

| Idea | In this repo |
| --- | --- |
| **Closure**: an inner function remembers names of the enclosing scope | `loan_closed_handler(notifier)` in `notifications.py` |
| **Decorator**: a function that takes a function and returns a function | `@require_api_key` in `api/auth.py` |
| Late binding: a closure reads the variable when it is CALLED, not when it was made | `[lambda: i for i in range(3)]` all return 2 |
| `*args`, `**kwargs`, keyword-only after `*` | `create_app(config, *, today=..., events=...)` |
| `functools`: `partial`, `lru_cache`, `wraps`, `total_ordering`, `singledispatch` | |

## Learn: iterators and generators

An **iterator** gives one value at a time (`next()`), then raises `StopIteration`. A **generator**
function (`yield`) is the easy way to write one. It is **lazy**: nothing runs until someone asks for
the next value, and memory stays flat however big the data is.

```python
def read_rows(source):         # loanlab/importer/extract.py
    for row in reader:
        yield RawRow(...)      # pauses here until the caller asks for the next row

rows = read_rows(file)         # nothing read yet
first = next(rows)             # reads ONE row
```

- `yield from other()` delegates to another generator (see `read_file`).
- A generator is used up after one pass: `g = (x for x in xs); sum(g); sum(g)` gives the total, then 0.
- `itertools`: `islice`, `chain`, `groupby` (input must be sorted by the key), `batched` (3.12).

## Learn: context managers and exceptions

```python
with open(path, encoding="utf-8-sig", newline="") as f:   # closed even if an exception escapes
    ...

@contextlib.contextmanager
def count_queries(session):   # tests/exercises/test_loan_repository.py
    event.listen(...)
    try:
        yield statements      # the body of the `with` runs here
    finally:
        event.remove(...)     # always runs
```

| Rule | Why |
| --- | --- |
| Catch the narrowest exception you can handle | `except Exception: pass` hides bugs (lesson 18) |
| `raise NewError(...) from exc` | Keeps the original cause in the traceback (`credit.py`) |
| `try / except / else / finally` | `else` runs only if no exception; `finally` always |
| EAFP: "easier to ask forgiveness" | Pythonic: try it and catch `KeyError`, rather than check first (LBYL). Also avoids races. |
| Own exception hierarchy | `errors.py`: one base class, the API maps each subclass to a status code |
| `return` in `finally` | Overrides the `return` in `try`, and swallows exceptions. Never do it. |

## Learn: classes the modern way

| Tool | Use |
| --- | --- |
| `@dataclass(frozen=True, slots=True)` | Value objects: `__init__`, `__repr__`, `__eq__`, `__hash__` written for you |
| `field(default_factory=list)` | A fresh list per instance (`InMemoryNotifier`). `= []` would be shared. |
| `typing.Protocol` | Structural interface: anything with the right methods fits (`EventLog`, `CreditBureau`) |
| `abc.ABC` + `@abstractmethod` | Nominal interface: must inherit; cannot instantiate an incomplete subclass |
| `enum.Enum` / `IntEnum` / `StrEnum` | Closed set of values. `Outcome` is an `IntEnum`, so `max()` picks the worst |
| `@property` | Computed attribute (`Decision.approved`) |
| `@classmethod` / `@staticmethod` | Alternative constructor (`RuleResult.ok()`) / plain function in the class namespace |
| `super()` and the MRO | Method resolution order with multiple inheritance: `Class.__mro__` |
| Class attribute vs instance attribute | `class A: items = []` is shared by ALL instances |

Type hints are not checked at run time. `mypy` checks them. Use them at module boundaries.

**The GIL** (one thread runs Python bytecode at a time; lesson 07): threads help for I/O, not for
CPU work. For CPU: processes, or C code (NumPy). Python 3.13 has an experimental free-threaded build.

## In this repo

| File | Shows |
| --- | --- |
| `loanlab/products.py` | frozen + slots dataclass, a dict as an index (`_BY_CODE`) |
| `loanlab/errors.py` | exception hierarchy with class attributes |
| `loanlab/events.py`, `credit.py` | `Protocol`s, `threading.Lock` used as a context manager |
| `loanlab/eligibility.py` | `IntEnum`, `@property`, `@classmethod`, frozen dataclasses holding callables |
| `loanlab/notifications.py` | closures, `field(default_factory=...)`, `defaultdict` |
| `loanlab/importer/extract.py` | generators, `yield from`, `with` |

## Do

### 1. Predict, then run

In a REPL, write your prediction first, then run each line. Put the surprises in `notes/day-6.md`
with a one-line "why", like you did on day 1.

```python
t = (1, [2]); t[1] += [3]          # what happens? and what is t afterwards?
{1: "a", True: "b"}
[f() for f in [lambda: i for i in range(3)]]
g = (x * x for x in range(3)); sum(g), sum(g)
def f():
    try:
        return "try"
    finally:
        return "finally"
f()
class A: tags = []
a, b = A(), A(); a.tags.append("x"); b.tags
sorted(["b", "a", "C"]), sorted(["b", "a", "C"], key=str.lower)
Decimal("1.10") == Decimal("1.1"), hash(Decimal("1.10")) == hash(Decimal("1.1"))
[] is [], () is ()
```

### 2. Exercise: a `Money` value object

`exercises/money_value.py` describes the behaviour; the tests are in
`tests/exercises/test_money_value.py`. Write the class **by hand**, without `@dataclass`, so you
meet each dunder method. Run `pytest -m exercise tests/exercises/test_money_value.py` until green.
Then answer: why must `__eq__` return `NotImplemented` (not `False`) for a non-Money? What breaks
if `__hash__` uses a mutable field?

### 3. A decorator

Write `@timed` in `notes/timed.py`: it logs `"<function name> took 12.3 ms"` with `time.perf_counter`.
Use `functools.wraps` and check that `__name__` is kept. Then make it `@timed(threshold_ms=100)`,
logging only slow calls. How many nested functions does that need, and why?

### 4. A generator pipeline

Using `read_file`, print the number of rows of `data/branch-iasi-2026-03.csv` per product code
without building a list of rows. Use `collections.Counter` and a generator expression.

## Check yourself

1. "Python passes arguments by reference." True? Explain with a list and with an int.
2. Why is a mutable default argument a bug? Show the fix.
3. What is a closure? What is late binding, and how do you work around it in a loop?
4. Write a decorator that takes arguments. Why `functools.wraps`?
5. Iterator vs iterable vs generator. What happens on the second pass over a generator?
6. What does `with` do? Write a context manager with `contextlib.contextmanager`.
7. `__eq__` without `__hash__`: what happens to instances? Why do equal objects need equal hashes?
8. `Protocol` vs `ABC`: when would you choose each?
9. `@staticmethod` vs `@classmethod`: one use of each.
10. What is the GIL, and when does it matter?

## Say it in the interview

- "In Python a variable is a name bound to an object. Arguments are passed as object references:
  mutating a list inside a function is visible outside, rebinding the name is not."
- "I build value objects as frozen dataclasses, so they get equality and hashing right. When I need
  the operators to behave like a number, I implement the dunder methods and return NotImplemented
  for types I don't support."
- "I use generators for anything that streams, like reading a big file or exporting a report: the
  memory stays flat and the first row goes out immediately."

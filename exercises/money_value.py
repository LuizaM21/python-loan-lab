"""Lesson 11 exercise: a Money value object, built with Python's data model (dunder methods).

Tests: tests/exercises/test_money_value.py    Run: pytest -m exercise tests/exercises/test_money_value.py

Write the class by hand (no @dataclass) so you meet each dunder method once. Behaviour:

- Money(amount, currency="RON"). `amount` is a Decimal, int or str; it is rounded half-up to 0.01.
  A float is a TypeError (money never passes through float). Currency is upper-cased: "ron" -> "RON".
- Immutable: assigning an attribute after construction raises AttributeError. Use __slots__.
- repr(Money("10.5")) == "Money('10.50', 'RON')"; str(Money("10.5")) == "10.50 RON".
- == compares amount and currency. Money == 10 is False (not an error). Equal values have equal hashes,
  so Money works in sets and as dict keys.
- <, <=, >, >= work within one currency (tip: functools.total_ordering). Another currency raises
  CurrencyMismatch. Comparing with a non-Money: return NotImplemented (Python then raises TypeError).
- a + b and a - b within one currency -> Money. Another currency -> CurrencyMismatch.
- sum([Money("1"), Money("2")]) works: sum() starts with 0, so 0 + Money must work (__radd__).
- Money * int or Decimal (either order) -> Money, rounded half-up. -Money negates.
- bool(Money("0")) is False, any other amount is True.
- allocate(n) splits into n parts that add up EXACTLY to the original; the first parts get the
  extra cents: Money("100").allocate(3) -> [33.34, 33.33, 33.33]. n < 1 -> ValueError.
"""

from __future__ import annotations


class CurrencyMismatch(ValueError):
    pass


class Money:
    pass  # TODO lesson 11: write the whole class (start with __init__ and __slots__)

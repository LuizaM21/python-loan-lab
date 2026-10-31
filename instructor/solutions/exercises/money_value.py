"""Reference solution, lesson 11: Money value object."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from functools import total_ordering
from typing import Any

CENT = Decimal("0.01")


class CurrencyMismatch(ValueError):
    pass


@total_ordering
class Money:
    __slots__ = ("amount", "currency")

    amount: Decimal
    currency: str

    def __init__(self, amount: Decimal | int | str, currency: str = "RON") -> None:
        if isinstance(amount, float):
            raise TypeError("Money needs Decimal, int or str, never float.")
        # object.__setattr__ because our own __setattr__ forbids assignment
        object.__setattr__(self, "amount", Decimal(amount).quantize(CENT, rounding=ROUND_HALF_UP))
        object.__setattr__(self, "currency", currency.upper())

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Money is immutable.")

    def __repr__(self) -> str:
        return f"Money('{self.amount}', '{self.currency}')"

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return (self.amount, self.currency) == (other.amount, other.currency)

    def __hash__(self) -> int:
        return hash((self.amount, self.currency))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._same_currency(other)
        return self.amount < other.amount

    def __add__(self, other: object) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        self._same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __radd__(self, other: object) -> Money:
        if other == 0:  # sum() starts with 0
            return self
        return self.__add__(other)

    def __sub__(self, other: object) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        self._same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: object) -> Money:
        if isinstance(factor, bool) or not isinstance(factor, (int, Decimal)):
            return NotImplemented
        return Money(self.amount * factor, self.currency)

    __rmul__ = __mul__

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def __bool__(self) -> bool:
        return self.amount != 0

    def allocate(self, parts: int) -> list[Money]:
        if parts < 1:
            raise ValueError("parts must be at least 1")
        cents = int(self.amount / CENT)
        base, extra = divmod(cents, parts)
        return [Money(Decimal(base + (1 if i < extra else 0)) * CENT, self.currency) for i in range(parts)]

    def _same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatch(f"{self.currency} vs {other.currency}")

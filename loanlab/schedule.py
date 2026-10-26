"""Repayment schedule maths. Pure functions: no database, no HTTP, no clock.

Rules (see CLAUDE.md, Domain rules):
- monthly rate r = annual rate / 12
- monthly payment = amount * r / (1 - (1 + r) ** -months), rounded half-up to 0.01
  (with a 0% rate: amount / months, rounded half-up)
- each month: interest = balance * r rounded half-up; principal = payment - interest
- the last month repays whatever is left, so the final balance is exactly 0.00
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .money import to_money


@dataclass(frozen=True, slots=True)
class Instalment:
    month: int
    payment: Decimal
    interest: Decimal
    principal: Decimal
    balance: Decimal


@dataclass(frozen=True, slots=True)
class Schedule:
    monthly_payment: Decimal
    instalments: tuple[Instalment, ...]


def monthly_payment(amount: Decimal, annual_rate: Decimal, months: int) -> Decimal:
    if months < 1:
        raise ValueError("months must be at least 1")
    if annual_rate == 0:
        return to_money(amount / months)
    r = annual_rate / 12
    return to_money(amount * r / (1 - (1 + r) ** -months))


def calculate(amount: Decimal, annual_rate: Decimal, months: int) -> Schedule:
    payment = monthly_payment(amount, annual_rate, months)
    r = annual_rate / 12
    balance = amount
    instalments = []
    for month in range(1, months + 1):
        interest = to_money(balance * r)
        # the last month repays whatever is left, so the balance ends at exactly 0.00
        principal = balance if month == months else payment - interest
        balance = to_money(balance - principal)
        instalments.append(
            Instalment(
                month=month,
                payment=to_money(principal + interest),
                interest=interest,
                principal=to_money(principal),
                balance=balance,
            )
        )
    return Schedule(monthly_payment=payment, instalments=tuple(instalments))

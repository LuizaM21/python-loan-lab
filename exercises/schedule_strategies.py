"""Lesson 14 exercise: the Strategy pattern for repayment schedules.

Tests: tests/exercises/test_schedule_strategies.py   Run: pytest -m exercise tests/exercises/test_schedule_strategies.py

Today every loan is an ANNUITY: the same payment every month (loanlab/schedule.py). The product team
wants a second method, EQUAL PRINCIPAL: the same principal every month, so payments start high and
go down. Later they may want more. Each method is a Strategy: same interface, different algorithm,
chosen at run time by name.

Equal principal rules (r = annual_rate / 12, all amounts rounded half-up to 0.01):
- principal per month = amount / months
- each month: interest = balance x r; payment = principal + interest
- the LAST month's principal is whatever balance is left, so the final balance is exactly 0.00
- Schedule.monthly_payment = the FIRST month's payment (the highest one)
- annual_rate 0 works (interest 0.00 every month)

Worked example (do it by hand first!): 1,200.00 at 12% for 12 months: r = 0.01, principal 100.00.
Month 1: interest 12.00, payment 112.00, balance 1,100.00. Month 2: 11.00, 111.00, 1,000.00 ...
Month 12: interest 1.00, payment 101.00, balance 0.00.

Then: `strategy_for(name)` returns the strategy registered under that name ("annuity",
"equal_principal"), case-insensitive; an unknown name raises ValueError listing the known names.
Adding a third strategy must mean adding a class and one registry line, nothing else.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from loanlab import schedule
from loanlab.schedule import Schedule


class ScheduleStrategy(Protocol):
    name: str

    def calculate(self, amount: Decimal, annual_rate: Decimal, months: int) -> Schedule: ...


class AnnuityStrategy:
    name = "annuity"

    def calculate(self, amount: Decimal, annual_rate: Decimal, months: int) -> Schedule:
        return schedule.calculate(amount, annual_rate, months)


class EqualPrincipalStrategy:
    name = "equal_principal"

    def calculate(self, amount: Decimal, annual_rate: Decimal, months: int) -> Schedule:
        raise NotImplementedError  # TODO lesson 14


def strategy_for(name: str) -> ScheduleStrategy:
    raise NotImplementedError  # TODO lesson 14

"""Reference solution, lesson 14: Strategy + registry."""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from loanlab import schedule
from loanlab.money import to_money
from loanlab.schedule import Instalment, Schedule


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
        if months < 1:
            raise ValueError("months must be at least 1")
        r = annual_rate / 12
        principal = to_money(amount / months)
        balance = amount
        instalments = []
        for month in range(1, months + 1):
            interest = to_money(balance * r)
            this_principal = balance if month == months else principal
            balance = to_money(balance - this_principal)
            instalments.append(
                Instalment(
                    month=month,
                    payment=to_money(this_principal + interest),
                    interest=interest,
                    principal=to_money(this_principal),
                    balance=balance,
                )
            )
        return Schedule(monthly_payment=instalments[0].payment, instalments=tuple(instalments))


_STRATEGIES: dict[str, ScheduleStrategy] = {s.name: s for s in (AnnuityStrategy(), EqualPrincipalStrategy())}


def strategy_for(name: str) -> ScheduleStrategy:
    try:
        return _STRATEGIES[name.strip().lower()]
    except KeyError:
        raise ValueError(f"Unknown schedule {name!r}. Known: {', '.join(sorted(_STRATEGIES))}.") from None

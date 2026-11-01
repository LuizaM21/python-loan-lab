"""Reference solution, lesson 12: a new rule, added without editing loanlab/eligibility.py (OCP)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from loanlab.eligibility import Application, Outcome, RuleResult


@dataclass(frozen=True)
class FirstLoanCap:
    count_all_loans: Callable[[str], int]
    cap: Decimal = Decimal("15000.00")

    def check(self, application: Application) -> RuleResult:
        if application.amount <= self.cap:
            return RuleResult.ok()  # cheap check first: no lookup needed
        if self.count_all_loans(application.customer_name) > 0:
            return RuleResult.ok()
        return RuleResult(Outcome.REFER, f"First loan above {self.cap} RON needs manual review.")

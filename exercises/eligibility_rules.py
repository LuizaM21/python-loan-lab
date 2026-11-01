"""Lesson 12 exercise: add a rule to the eligibility policy WITHOUT editing loanlab/eligibility.py.

Tests: tests/exercises/test_first_loan_cap.py   Run: pytest -m exercise tests/exercises/test_first_loan_cap.py

Rule (from the risk team): a customer who has NEVER had a loan with us (active or closed) may borrow
at most 15,000.00 RON without a human looking at it. Above that: REFER, with the reason
"First loan above 15000.00 RON needs manual review." Exactly 15,000.00 is fine (limits are inclusive).
Customers with any earlier loan: this rule always approves.

Design constraints (this is the point of the exercise):
- The rule satisfies the EligibilityRule Protocol: one method, check(application) -> RuleResult.
- It does not import SQLAlchemy and does not take a Session. It takes `count_all_loans`, a function
  from customer name to number of loans. The app passes a repository method; tests pass a lambda.
- The cap is a constructor argument with 15000.00 as the default, so a different market can reuse it.
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from loanlab.eligibility import Application, RuleResult


class FirstLoanCap:
    def __init__(self, count_all_loans: Callable[[str], int], cap: Decimal = Decimal("15000.00")) -> None:
        raise NotImplementedError  # TODO lesson 12

    def check(self, application: Application) -> RuleResult:
        raise NotImplementedError  # TODO lesson 12

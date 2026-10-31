"""Loan eligibility: may this customer get this loan? Lessons 12 (composition, SOLID) and 14 (patterns).

Design in one sentence: a policy is COMPOSED of small rules; each rule answers one question.

- Single responsibility: each rule checks one thing.
- Open/closed: a new rule is a new class; `EligibilityPolicy` does not change.
- Liskov: every rule honours the same contract (returns a RuleResult, never raises for a "no").
- Interface segregation: a rule needs only `check()`; `MaxActiveLoans` needs only a counting function,
  not a whole Session or repository.
- Dependency inversion: rules depend on `CreditBureau` (a Protocol) and on a plain callable, never
  on HTTP or SQLAlchemy. The app wires the real ones in; tests pass fakes.

Patterns: Chain of Responsibility (rules run in order, a REJECT stops the chain), Composite
(the policy looks like one rule from outside), Null Object (`AllowAll`).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum
from typing import Protocol

from .credit import CreditBureau, CreditBureauRejected, CreditBureauUnavailable
from .products import find_product
from .schedule import monthly_payment


class Outcome(IntEnum):
    """Ordered by severity, so the worst outcome is simply max()."""

    APPROVE = 0
    REFER = 1  # a human must look at it (manual review)
    REJECT = 2


@dataclass(frozen=True, slots=True)
class Application:
    customer_name: str
    product_code: str
    amount: Decimal
    months: int
    monthly_income: Decimal


@dataclass(frozen=True, slots=True)
class RuleResult:
    outcome: Outcome
    reason: str = ""

    @classmethod
    def ok(cls) -> RuleResult:
        return cls(Outcome.APPROVE)


@dataclass(frozen=True, slots=True)
class Decision:
    outcome: Outcome
    reasons: tuple[str, ...] = ()

    @property
    def approved(self) -> bool:
        return self.outcome is Outcome.APPROVE


class EligibilityRule(Protocol):
    def check(self, application: Application) -> RuleResult: ...


# ----------------------------------------------------------------------------- rules


class KnownProduct:
    """Cheap and first: the other rules need a valid product."""

    def check(self, application: Application) -> RuleResult:
        if find_product(application.product_code) is None:
            return RuleResult(Outcome.REJECT, "Unknown loan product.")
        return RuleResult.ok()


@dataclass(frozen=True)
class MaxDebtToIncome:
    """The new monthly payment may take at most `limit` of the monthly income (0.40 = 40%)."""

    limit: Decimal = Decimal("0.40")

    def check(self, application: Application) -> RuleResult:
        product = find_product(application.product_code)
        if product is None:
            return RuleResult(Outcome.REJECT, "Unknown loan product.")
        if application.monthly_income <= 0:
            return RuleResult(Outcome.REJECT, "Monthly income must be positive.")
        payment = monthly_payment(application.amount, product.annual_rate, application.months)
        if payment > application.monthly_income * self.limit:
            return RuleResult(
                Outcome.REJECT,
                f"Monthly payment {payment} RON is more than {self.limit:.0%} of the income.",
            )
        return RuleResult.ok()


@dataclass(frozen=True)
class MaxActiveLoans:
    """At most `limit` active loans per customer. Counting is injected: no Session in here."""

    count_active: Callable[[str], int]
    limit: int = 3

    def check(self, application: Application) -> RuleResult:
        if self.count_active(application.customer_name) >= self.limit:
            return RuleResult(Outcome.REJECT, f"Customer already has {self.limit} active loans.")
        return RuleResult.ok()


@dataclass(frozen=True)
class MinCreditScore:
    """Asks the bureau. If the bureau is down we do not guess: we REFER (graceful degradation)."""

    bureau: CreditBureau
    minimum: int = 600

    def check(self, application: Application) -> RuleResult:
        try:
            report = self.bureau.report(application.customer_name)
        except CreditBureauUnavailable:
            return RuleResult(Outcome.REFER, "Credit bureau unavailable: manual review needed.")
        except CreditBureauRejected as exc:
            return RuleResult(Outcome.REFER, f"No usable credit report: {exc}")
        if report.score < self.minimum:
            return RuleResult(Outcome.REJECT, f"Credit score {report.score} is below {self.minimum}.")
        return RuleResult.ok()


# ----------------------------------------------------------------------------- policies


class EligibilityPolicy:
    """Runs the rules in order (put cheap rules first, the remote call last).

    A REJECT stops the chain: no point paying for a bureau call when the income check already
    failed. REFER does not stop it: we collect every reason for the human reviewer.
    """

    def __init__(self, rules: Sequence[EligibilityRule]) -> None:
        self._rules = tuple(rules)

    def decide(self, application: Application) -> Decision:
        outcome = Outcome.APPROVE
        reasons: list[str] = []
        for rule in self._rules:
            result = rule.check(application)
            outcome = max(outcome, result.outcome)
            if result.reason:
                reasons.append(result.reason)
            if result.outcome is Outcome.REJECT:
                break
        return Decision(outcome, tuple(reasons))


class AllowAll:
    """Null Object: a policy that approves everything. Callers never have to check for None."""

    def decide(self, application: Application) -> Decision:
        return Decision(Outcome.APPROVE)


def default_policy(bureau: CreditBureau, count_active: Callable[[str], int]) -> EligibilityPolicy:
    """Factory: the one place that knows which rules make up the standard policy, and in which order."""
    return EligibilityPolicy(
        [
            KnownProduct(),
            MaxDebtToIncome(),
            MaxActiveLoans(count_active),
            MinCreditScore(bureau),  # remote and slow: last
        ]
    )

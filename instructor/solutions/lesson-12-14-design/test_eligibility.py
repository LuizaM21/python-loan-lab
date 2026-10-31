"""Reference tests for loanlab/eligibility.py (lessons 12 and 14). Fakes, not mocks: our own code."""

from __future__ import annotations

from decimal import Decimal

import pytest

from loanlab.credit import CreditBureauRejected, CreditBureauUnavailable, CreditReport
from loanlab.eligibility import (
    AllowAll,
    Application,
    EligibilityPolicy,
    KnownProduct,
    MaxActiveLoans,
    MaxDebtToIncome,
    MinCreditScore,
    Outcome,
    RuleResult,
    default_policy,
)


class FakeBureau:
    """A fake: a tiny working implementation with knobs. Counts calls so tests can check the chain."""

    def __init__(self, score: int = 700, error: Exception | None = None) -> None:
        self.score = score
        self.error = error
        self.calls = 0

    def report(self, customer_name: str) -> CreditReport:
        self.calls += 1
        if self.error:
            raise self.error
        return CreditReport(customer_name, self.score, Decimal("0.00"))


def application(amount: str = "10000.00", months: int = 12, income: str = "5000.00", code: str = "PERS") -> Application:
    return Application("Ana Pop", code, Decimal(amount), months, Decimal(income))


class TestMaxDebtToIncome:
    # PERS 10,000.00 over 12 months: payment 878.69 (README). 40% of income must cover it.
    @pytest.mark.parametrize(("income", "outcome"), [("2196.73", Outcome.APPROVE), ("2196.72", Outcome.REJECT)])
    def test_boundary_on_the_income(self, income, outcome):
        # 878.69 / 0.40 = 2196.725 -> 2196.73 * 0.40 = 878.692 >= 878.69; 2196.72 * 0.40 = 878.688 < 878.69
        assert MaxDebtToIncome().check(application(income=income)).outcome is outcome

    def test_rejects_zero_income(self):
        assert MaxDebtToIncome().check(application(income="0")).outcome is Outcome.REJECT


class TestMaxActiveLoans:
    @pytest.mark.parametrize(("active", "outcome"), [(2, Outcome.APPROVE), (3, Outcome.REJECT)])
    def test_limit(self, active, outcome):
        assert MaxActiveLoans(lambda name: active).check(application()).outcome is outcome


class TestMinCreditScore:
    @pytest.mark.parametrize(("score", "outcome"), [(600, Outcome.APPROVE), (599, Outcome.REJECT)])
    def test_minimum_score(self, score, outcome):
        assert MinCreditScore(FakeBureau(score)).check(application()).outcome is outcome

    @pytest.mark.parametrize("error", [CreditBureauUnavailable("down"), CreditBureauRejected("no history")])
    def test_refers_to_a_human_when_the_bureau_cannot_help(self, error):
        result = MinCreditScore(FakeBureau(error=error)).check(application())

        assert result.outcome is Outcome.REFER


class TestEligibilityPolicy:
    def test_approves_when_every_rule_approves(self):
        policy = default_policy(FakeBureau(), count_active=lambda name: 0)

        assert policy.decide(application()).approved

    def test_a_reject_stops_the_chain_before_the_expensive_call(self):
        bureau = FakeBureau()
        policy = default_policy(bureau, count_active=lambda name: 0)

        decision = policy.decide(application(income="100.00"))

        assert decision.outcome is Outcome.REJECT
        assert bureau.calls == 0

    def test_refer_does_not_stop_the_chain_and_collects_reasons(self):
        class AlwaysRefer:
            def check(self, application: Application) -> RuleResult:
                return RuleResult(Outcome.REFER, "first")

        policy = EligibilityPolicy([AlwaysRefer(), MinCreditScore(FakeBureau(error=CreditBureauUnavailable("x")))])

        decision = policy.decide(application())

        assert decision.outcome is Outcome.REFER
        assert len(decision.reasons) == 2

    def test_unknown_product_is_rejected_first(self):
        decision = EligibilityPolicy([KnownProduct(), MaxDebtToIncome()]).decide(application(code="CARD"))

        assert decision.reasons == ("Unknown loan product.",)

    def test_null_object_approves_everything(self):
        assert AllowAll().decide(application(income="1.00")).approved

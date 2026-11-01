from decimal import Decimal

import pytest

from exercises.eligibility_rules import FirstLoanCap
from loanlab.eligibility import Application, EligibilityPolicy, KnownProduct, MaxDebtToIncome, Outcome

pytestmark = pytest.mark.exercise


def application(amount: str, name: str = "Ana Pop") -> Application:
    return Application(name, "PERS", Decimal(amount), 60, monthly_income=Decimal("20000.00"))


class TestFirstLoanCap:
    @pytest.mark.parametrize("amount", ["1000.00", "15000.00"])
    def test_approves_a_first_loan_up_to_the_cap(self, amount):
        # setup

        rule = FirstLoanCap(count_all_loans=lambda name: 0)

        # execute

        result = rule.check(application(amount))

        # verify

        assert result.outcome is Outcome.APPROVE

    def test_refers_a_first_loan_one_cent_above_the_cap(self):
        # setup

        rule = FirstLoanCap(count_all_loans=lambda name: 0)

        # execute

        result = rule.check(application("15000.01"))

        # verify

        assert result.outcome is Outcome.REFER
        assert result.reason == "First loan above 15000.00 RON needs manual review."

    def test_ignores_the_cap_for_a_returning_customer(self):
        # setup

        rule = FirstLoanCap(count_all_loans=lambda name: 1)

        # execute

        result = rule.check(application("40000.00"))

        # verify

        assert result.outcome is Outcome.APPROVE

    def test_the_cap_is_configurable(self):
        # setup

        rule = FirstLoanCap(count_all_loans=lambda name: 0, cap=Decimal("5000.00"))

        # execute

        result = rule.check(application("5000.01"))

        # verify

        assert result.outcome is Outcome.REFER
        assert "5000.00" in result.reason

    def test_asks_about_the_applicant_by_name(self):
        # setup

        asked: list[str] = []
        rule = FirstLoanCap(count_all_loans=lambda name: asked.append(name) or 0)

        # execute

        rule.check(application("20000.00", name="Ion Rusu"))

        # verify

        assert asked == ["Ion Rusu"]

    def test_plugs_into_the_existing_policy_unchanged(self):
        # setup

        policy = EligibilityPolicy([KnownProduct(), MaxDebtToIncome(), FirstLoanCap(lambda name: 0)])

        # execute

        decision = policy.decide(application("20000.00"))

        # verify

        assert decision.outcome is Outcome.REFER
        assert decision.reasons == ("First loan above 15000.00 RON needs manual review.",)

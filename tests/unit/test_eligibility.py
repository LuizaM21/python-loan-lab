from decimal import Decimal

from loanlab.credit import CreditBureauUnavailable, CreditReport
from loanlab.eligibility import Application, MinCreditScore, Outcome


class FakeBureau:
    """A fake: a tiny working CreditBureau. No Mock needed for our own Protocol."""

    def __init__(self, score: int = 700, error: Exception | None = None) -> None:
        self.score = score
        self.error = error

    def report(self, customer_name: str) -> CreditReport:
        if self.error:
            raise self.error
        return CreditReport(customer_name, self.score, Decimal("0.00"))


class TestMinCreditScore:
    def test_refers_to_a_human_when_the_bureau_is_down(self):
        # setup

        rule = MinCreditScore(FakeBureau(error=CreditBureauUnavailable("timeout")))
        application = Application("Ana Pop", "PERS", Decimal("10000.00"), 12, Decimal("5000.00"))

        # execute

        result = rule.check(application)

        # verify

        assert result.outcome is Outcome.REFER

    # Lessons 12 and 14: add your own tests below this line (boundaries, the chain, the policy).

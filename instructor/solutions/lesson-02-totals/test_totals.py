"""Lesson 02 reference tests (written BEFORE the feature, TDD). Copy into tests/unit and tests/api.

Expected values by hand for 10000.00 PERS over 12 months:
  11 x 878.69 + 878.74 = 10544.33 paid in total, so 544.33 is interest.
"""

from decimal import Decimal

from loanlab import schedule


class TestScheduleTotals:
    def test_total_paid_is_the_sum_of_all_payments(self):
        result = schedule.calculate(Decimal("10000.00"), Decimal("0.0990"), 12)
        assert result.total_paid == Decimal("10544.33")

    def test_total_interest_is_total_paid_minus_the_amount(self):
        result = schedule.calculate(Decimal("10000.00"), Decimal("0.0990"), 12)
        assert result.total_interest == Decimal("544.33")
        assert result.total_paid - result.total_interest == Decimal("10000.00")

    def test_a_zero_rate_has_no_interest(self):
        result = schedule.calculate(Decimal("1200.00"), Decimal("0"), 12)
        assert result.total_interest == Decimal("0.00")


class TestQuoteTotalsApi:
    def test_quote_shows_the_totals(self, client):
        body = client.post("/api/loans/quote", json={"productCode": "PERS", "amount": 10000, "months": 12}).get_json()
        assert body["totalPaid"] == "10544.33"
        assert body["totalInterest"] == "544.33"

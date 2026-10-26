"""Reference unit tests for loanlab/schedule.py. Expected values worked out by hand from the rules."""

from decimal import Decimal

import pytest

from loanlab import schedule

D = Decimal


class TestScheduleSolution:
    def test_pays_the_same_amount_every_month_except_the_last(self):
        # setup

        amount, rate, months = D("10000.00"), D("0.0990"), 12

        # execute

        result = schedule.calculate(amount, rate, months)

        # verify

        assert result.monthly_payment == D("878.69")
        assert result.instalments[0].interest == D("82.50")  # 10000 * 0.0099/12 = 82.50
        assert result.instalments[0].principal == D("796.19")
        assert result.instalments[0].balance == D("9203.81")
        assert result.instalments[-1].payment == D("878.74")
        assert result.instalments[-1].balance == D("0.00")

    @pytest.mark.parametrize(
        ("amount", "rate", "months"),
        [(D("1000.00"), D("0.0990"), 6), (D("50000.00"), D("0.0990"), 60), (D("123456.78"), D("0.0550"), 360)],
    )
    def test_repays_exactly_the_borrowed_amount(self, amount, rate, months):
        # execute

        result = schedule.calculate(amount, rate, months)

        # verify

        assert sum(i.principal for i in result.instalments) == amount
        assert result.instalments[-1].balance == D("0.00")
        assert [i.month for i in result.instalments] == list(range(1, months + 1))

    def test_a_zero_rate_splits_the_amount_evenly(self):
        # execute

        result = schedule.calculate(D("1200.00"), D("0"), 12)

        # verify

        assert result.monthly_payment == D("100.00")
        assert all(i.interest == D("0.00") for i in result.instalments)

    def test_one_month_repays_amount_plus_one_month_of_interest(self):
        # execute

        result = schedule.calculate(D("1200.00"), D("0.1200"), 1)

        # verify

        assert result.monthly_payment == D("1212.00")
        assert result.instalments[0].payment == D("1212.00")

    def test_rejects_zero_months(self):
        with pytest.raises(ValueError):
            schedule.calculate(D("1000"), D("0.05"), 0)

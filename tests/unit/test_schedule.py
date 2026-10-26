from decimal import Decimal

from loanlab import schedule


class TestSchedule:
    def test_pays_the_same_amount_every_month_except_the_last(self):
        # setup

        amount, annual_rate, months = Decimal("10000.00"), Decimal("0.0990"), 12

        # execute

        result = schedule.calculate(amount, annual_rate, months)

        # verify

        assert result.monthly_payment == Decimal("878.69")
        assert [i.payment for i in result.instalments[:-1]] == [Decimal("878.69")] * 11
        assert result.instalments[-1].payment == Decimal("878.74")
        assert result.instalments[-1].balance == Decimal("0.00")

    # Add your own tests below this line.

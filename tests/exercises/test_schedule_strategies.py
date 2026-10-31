from decimal import Decimal

import pytest

from exercises.schedule_strategies import AnnuityStrategy, EqualPrincipalStrategy, strategy_for
from loanlab import schedule

pytestmark = pytest.mark.exercise

D = Decimal


def rows(result):
    return [(i.month, i.payment, i.interest, i.principal, i.balance) for i in result.instalments]


class TestEqualPrincipalStrategy:
    def test_pays_the_same_principal_each_month_and_interest_goes_down(self):
        # setup

        strategy = EqualPrincipalStrategy()

        # execute

        result = strategy.calculate(D("1200.00"), D("0.12"), 12)

        # verify

        table = rows(result)
        assert table[0] == (1, D("112.00"), D("12.00"), D("100.00"), D("1100.00"))
        assert table[1] == (2, D("111.00"), D("11.00"), D("100.00"), D("1000.00"))
        assert table[11] == (12, D("101.00"), D("1.00"), D("100.00"), D("0.00"))
        assert result.monthly_payment == D("112.00")
        assert sum(i.interest for i in result.instalments) == D("78.00")

    def test_the_last_month_repays_the_rounding_rest(self):
        # setup

        strategy = EqualPrincipalStrategy()

        # execute

        result = strategy.calculate(D("1000.00"), D("0.12"), 3)

        # verify

        assert rows(result) == [
            (1, D("343.33"), D("10.00"), D("333.33"), D("666.67")),
            (2, D("340.00"), D("6.67"), D("333.33"), D("333.34")),
            (3, D("336.67"), D("3.33"), D("333.34"), D("0.00")),
        ]

    def test_works_with_a_zero_rate(self):
        # setup

        strategy = EqualPrincipalStrategy()

        # execute

        result = strategy.calculate(D("1000.00"), D("0"), 3)

        # verify

        assert [i.payment for i in result.instalments] == [D("333.33"), D("333.33"), D("333.34")]
        assert all(i.interest == D("0.00") for i in result.instalments)


class TestStrategyRegistry:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("annuity", AnnuityStrategy),
            ("equal_principal", EqualPrincipalStrategy),
            ("EQUAL_PRINCIPAL", EqualPrincipalStrategy),
        ],
    )
    def test_finds_a_strategy_by_name(self, name, expected):
        assert isinstance(strategy_for(name), expected)

    def test_rejects_an_unknown_name_and_lists_the_known_ones(self):
        with pytest.raises(ValueError, match="annuity.*equal_principal"):
            strategy_for("balloon")

    def test_annuity_matches_the_existing_schedule(self):
        # setup

        amount, rate, months = D("10000.00"), D("0.0990"), 12

        # execute

        result = strategy_for("annuity").calculate(amount, rate, months)

        # verify

        assert result == schedule.calculate(amount, rate, months)
        assert result.monthly_payment == D("878.69")

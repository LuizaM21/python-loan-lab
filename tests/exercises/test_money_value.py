from decimal import Decimal

import pytest

from exercises.money_value import CurrencyMismatch, Money

pytestmark = pytest.mark.exercise


class TestMoneyConstruction:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("10", Decimal("10.00")),
            (10, Decimal("10.00")),
            ("2.345", Decimal("2.35")),
            (Decimal("2.344"), Decimal("2.34")),
        ],
    )
    def test_rounds_half_up_to_cents(self, raw, expected):
        assert Money(raw).amount == expected

    def test_rejects_a_float(self):
        with pytest.raises(TypeError):
            Money(0.1)  # type: ignore[arg-type]

    def test_upper_cases_the_currency(self):
        assert Money("1", "eur").currency == "EUR"

    def test_is_immutable(self):
        money = Money("1")
        with pytest.raises(AttributeError):
            money.amount = Decimal("2")  # type: ignore[misc]

    def test_repr_and_str(self):
        assert repr(Money("10.5")) == "Money('10.50', 'RON')"
        assert str(Money("10.5")) == "10.50 RON"


class TestMoneyEquality:
    def test_equal_amount_and_currency_are_equal(self):
        assert Money("10") == Money("10.00")

    def test_other_currency_is_not_equal(self):
        assert Money("10") != Money("10", "EUR")

    def test_comparing_with_a_number_is_false_not_an_error(self):
        assert (Money("10") == 10) is False

    def test_equal_values_work_in_a_set(self):
        assert len({Money("10"), Money("10.00"), Money("11")}) == 2


class TestMoneyOrdering:
    def test_orders_within_one_currency(self):
        assert Money("1") < Money("2") <= Money("2") < Money("3")
        assert max([Money("5"), Money("7"), Money("6")]) == Money("7")

    def test_other_currency_cannot_be_ordered(self):
        with pytest.raises(CurrencyMismatch):
            _ = Money("1") < Money("2", "EUR")

    def test_a_number_cannot_be_ordered(self):
        with pytest.raises(TypeError):
            _ = Money("1") < 2  # type: ignore[operator]


class TestMoneyArithmetic:
    def test_adds_and_subtracts(self):
        assert Money("10.10") + Money("0.20") == Money("10.30")
        assert Money("10.10") - Money("0.20") == Money("9.90")

    def test_cannot_add_another_currency(self):
        with pytest.raises(CurrencyMismatch):
            _ = Money("1") + Money("1", "EUR")

    def test_sum_works(self):
        assert sum([Money("1.10"), Money("2.20"), Money("3.30")]) == Money("6.60")

    @pytest.mark.parametrize("factor", [3, Decimal("3")])
    def test_multiplies_in_either_order(self, factor):
        assert Money("1.11") * factor == Money("3.33")
        assert factor * Money("1.11") == Money("3.33")

    def test_multiplication_rounds_half_up(self):
        assert Money("10.05") * Decimal("0.5") == Money("5.03")

    def test_negation_and_truthiness(self):
        assert -Money("5") == Money("-5")
        assert not Money("0")
        assert Money("0.01")


class TestMoneyAllocate:
    @pytest.mark.parametrize(
        ("total", "parts", "expected"),
        [
            ("100", 3, ["33.34", "33.33", "33.33"]),
            ("0.05", 3, ["0.02", "0.02", "0.01"]),
            ("10", 1, ["10.00"]),
            ("0.01", 2, ["0.01", "0.00"]),
        ],
    )
    def test_splits_into_parts_that_add_up_exactly(self, total, parts, expected):
        result = Money(total).allocate(parts)

        assert result == [Money(e) for e in expected]
        assert sum(result) == Money(total)

    def test_needs_at_least_one_part(self):
        with pytest.raises(ValueError):
            Money("1").allocate(0)

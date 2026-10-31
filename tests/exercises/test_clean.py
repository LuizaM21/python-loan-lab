from datetime import date
from decimal import Decimal

import pytest

from loanlab.importer.clean import (
    CleaningError,
    CleanLoanRow,
    canonical,
    clean_name,
    clean_product_code,
    clean_row,
    customer_key,
    parse_amount,
    parse_date,
    parse_months,
)

pytestmark = pytest.mark.exercise


class TestNames:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("Ana Pop", "Ana Pop"), ("  Ana   Pop ", "Ana Pop"), ("ana pop", "ana pop"), ("Ana\tPop", "Ana Pop")],
    )
    def test_trims_and_collapses_spaces_but_keeps_case(self, raw, expected):
        assert clean_name(raw) == expected

    @pytest.mark.parametrize("raw", [None, "", "   "])
    def test_rejects_an_empty_name(self, raw):
        with pytest.raises(CleaningError):
            clean_name(raw)

    def test_accepts_100_characters_and_rejects_101(self):
        assert clean_name("a" * 100) == "a" * 100
        with pytest.raises(CleaningError):
            clean_name("a" * 101)

    def test_the_key_ignores_case_and_spacing(self):
        assert customer_key("Ana Pop") == customer_key("  ANA   pop ") == "ana pop"


class TestAmounts:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("10000", "10000.00"),
            ("10000.50", "10000.50"),
            ("10000,50", "10000.50"),
            ("18000.5", "18000.50"),
            ("0,5", "0.50"),
            ("10,000.50", "10000.50"),
            ("10.000,50", "10000.50"),
            ("1 250,50", "1250.50"),
            ("1,250", "1250.00"),
            ("1.250", "1250.00"),
            ("1.250.000", "1250000.00"),
            ("1,250,000.75", "1250000.75"),
            ("1250 RON", "1250.00"),
            ("RON 1250", "1250.00"),
            ("1250 lei", "1250.00"),
            (" 45000 ron ", "45000.00"),
        ],
    )
    def test_reads_romanian_and_english_formats(self, raw, expected):
        result = parse_amount(raw)

        assert result == Decimal(expected)
        assert isinstance(result, Decimal)

    @pytest.mark.parametrize(
        "raw",
        [None, "", "abc", "-500", "0", "0,00", "10.5555", "1,250.555", "1.25.000", "12,34,567", ".5", "10.000.5"],
    )
    def test_rejects_what_it_cannot_read_safely(self, raw):
        with pytest.raises(CleaningError):
            parse_amount(raw)


class TestMonths:
    @pytest.mark.parametrize(("raw", "expected"), [("12", 12), (" 60 ", 60), ("1", 1)])
    def test_reads_a_whole_number(self, raw, expected):
        assert parse_months(raw) == expected

    @pytest.mark.parametrize("raw", [None, "", "0", "-12", "12.5", "twelve", "12 months"])
    def test_rejects_anything_else(self, raw):
        with pytest.raises(CleaningError):
            parse_months(raw)


class TestDates:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("2026-03-04", date(2026, 3, 4)),
            ("04/03/2026", date(2026, 3, 4)),
            ("04.03.2026", date(2026, 3, 4)),
            ("4/3/2026", date(2026, 3, 4)),
            ("13/03/2026", date(2026, 3, 13)),
        ],
    )
    def test_reads_iso_and_day_first(self, raw, expected):
        assert parse_date(raw) == expected

    @pytest.mark.parametrize("raw", [None, "", "2026-02-30", "13/13/2026", "03-04-2026", "March 4, 2026"])
    def test_rejects_impossible_or_unknown_dates(self, raw):
        with pytest.raises(CleaningError):
            parse_date(raw)


class TestProductCodes:
    def test_trims_and_upper_cases(self):
        assert clean_product_code(" pers ") == "PERS"

    def test_does_not_decide_if_the_product_exists(self):
        assert clean_product_code("card") == "CARD"

    @pytest.mark.parametrize("raw", [None, "", "  "])
    def test_rejects_an_empty_code(self, raw):
        with pytest.raises(CleaningError):
            clean_product_code(raw)


class TestRows:
    def test_maps_branch_headers_to_canonical_fields(self):
        values = {"nume_client": "Ana", "produs": "PERS", "suma": "1000", "luni": "12", "data": "2026-03-04"}

        assert canonical(values) == {
            "customer_name": "Ana",
            "product_code": "PERS",
            "amount": "1000",
            "months": "12",
            "opened_on": "2026-03-04",
        }

    def test_a_missing_column_becomes_empty(self):
        assert canonical({"customer": "Ana"})["amount"] == ""

    def test_cleans_a_good_row(self):
        values = {
            "customer": " Maria  Popescu",
            "product": "pers",
            "amount": "10.000,50",
            "term": "24",
            "date": "04.03.2026",
        }

        assert clean_row(values) == CleanLoanRow("Maria Popescu", "PERS", Decimal("10000.50"), 24, date(2026, 3, 4))

    def test_reports_every_problem_in_a_row_at_once(self):
        values = {
            "customer_name": "",
            "product_code": "PERS",
            "amount": "-5",
            "months": "twelve",
            "opened_on": "2026-03-04",
        }

        with pytest.raises(CleaningError) as raised:
            clean_row(values)

        problems = raised.value.problems
        assert len(problems) == 3
        assert [p.split(":")[0] for p in problems] == ["customer_name", "amount", "months"]

    def test_the_row_knows_its_deduplication_key(self):
        row = CleanLoanRow("Ana  POP", "PERS", Decimal("1000.00"), 12, date(2026, 3, 4))

        assert row.customer_key == "ana pop"

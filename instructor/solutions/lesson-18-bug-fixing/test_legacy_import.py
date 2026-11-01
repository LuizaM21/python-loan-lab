"""Reference solution, lesson 18: one regression test per ticket, plus characterization tests.

Copy to tests/unit/test_legacy_import.py. Each IMP test fails on the original legacy file and
passes after the fix. The characterization tests pass on both: they pin what already works,
so lesson 19 can refactor safely.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from loanlab.legacy.loan_import import import_file
from loanlab.models import Loan

HEADER = "customer_name,product_code,amount,months,opened_on\n"


@pytest.fixture
def write_csv(tmp_path: Path):
    def write(*lines: str, name: str = "branch.csv") -> Path:
        path = tmp_path / name
        path.write_text(HEADER + "".join(line + "\n" for line in lines), encoding="utf-8")
        return path

    return write


def loans(session: Session) -> list[Loan]:
    return list(session.scalars(select(Loan).order_by(Loan.id)))


class TestCharacterization:
    """What the importer already does right. Must stay green through every change."""

    def test_imports_a_plain_row_with_the_same_terms_as_the_service(self, session, write_csv):
        errors = import_file(session, write_csv("Ana Pop,PERS,10000,12,2026-03-02"), [])

        loan = loans(session)[0]
        assert errors == []
        assert (loan.reference, loan.customer_name, loan.product_code) == ("LN-0001", "Ana Pop", "PERS")
        assert (loan.amount, loan.outstanding, loan.monthly_payment) == (
            Decimal("10000.00"),
            Decimal("10000.00"),
            Decimal("878.69"),
        )
        assert (loan.status, loan.created_on, loan.months) == ("active", date(2026, 3, 2), 12)

    def test_product_codes_are_case_insensitive(self, session, write_csv):
        import_file(session, write_csv("Ion Rusu,auto,20000,24,2026-03-02"), [])

        assert loans(session)[0].product_code == "AUTO"

    def test_reports_an_unknown_product(self, session, write_csv):
        errors = import_file(session, write_csv("Ion Rusu,CARD,2000,12,2026-03-02"), [])

        assert loans(session) == []
        assert len(errors) == 1
        assert "CARD" in errors[0]

    def test_romanian_decimal_comma_works(self, session, write_csv):
        import_file(session, write_csv('Ana Pop,PERS,"10000,50",12,2026-03-02'), [])

        assert loans(session)[0].amount == Decimal("10000.50")


class TestTickets:
    def test_imp_101_amounts_with_thousands_separators_are_imported(self, session, write_csv):
        import_file(
            session, write_csv('Ana Pop,PERS,"1,250.50",6,2026-03-02', 'Ion Rusu,PERS,"10.000,50",12,2026-03-02')
        )

        assert [loan.amount for loan in loans(session)] == [Decimal("1250.50"), Decimal("10000.50")]

    def test_imp_101_a_row_that_cannot_be_read_is_reported_not_dropped(self, session, write_csv):
        errors = import_file(session, write_csv("Ana Pop,PERS,lots,6,2026-03-02"))

        assert loans(session) == []
        assert len(errors) == 1
        assert "line 2" in errors[0]

    def test_imp_102_dates_are_day_first(self, session, write_csv):
        import_file(session, write_csv("Ana Pop,PERS,10000,12,03/04/2026"))

        assert loans(session)[0].created_on == date(2026, 4, 3)

    def test_imp_103_each_import_has_its_own_error_list(self, session, write_csv):
        import_file(session, write_csv("Ana Pop,CARD,2000,12,2026-03-02", name="monday.csv"))

        errors = import_file(session, write_csv("Ion Rusu,PERS,2000,12,2026-03-03", name="tuesday.csv"))

        assert errors == []

    def test_imp_104_the_same_customer_with_other_spacing_or_case_is_a_duplicate(self, session, write_csv):
        errors = import_file(
            session, write_csv("Ana Pop,PERS,10000,12,2026-03-02", " ana  POP ,PERS,5000,12,2026-03-02")
        )

        assert [loan.customer_name for loan in loans(session)] == ["Ana Pop"]
        assert len(errors) == 1

    @pytest.mark.parametrize(
        "row",
        [
            "Radu Lungu,PERS,900000,12,2026-03-02",
            "Radu Lungu,PERS,10000,61,2026-03-02",
            "Radu Lungu,HOME,10000,60,2026-03-02",
        ],
    )
    def test_imp_105_product_limits_apply_to_imports(self, session, write_csv, row):
        errors = import_file(session, write_csv(row))

        assert loans(session) == []
        assert len(errors) == 1

    def test_imp_106_one_bad_date_does_not_lose_the_rest_of_the_file(self, session, write_csv):
        errors = import_file(
            session, write_csv("Vlad Dumitru,PERS,12000,36,2026-02-30", "Ioana Stan,PERS,18000,60,2026-03-09")
        )

        assert [loan.customer_name for loan in loans(session)] == ["Ioana Stan"]
        assert len(errors) == 1
        assert "line 2" in errors[0]

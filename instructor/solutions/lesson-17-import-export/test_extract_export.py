"""Reference tests for loanlab/importer/extract.py and export.py (lesson 17)."""

from __future__ import annotations

import io
from decimal import Decimal
from pathlib import Path

from loanlab.importer.export import REPORT_COLUMNS, loan_report_rows, write_csv
from loanlab.importer.extract import read_file, read_rows

DATA = Path(__file__).resolve().parents[2] / "data"  # after you copy this file to tests/unit/


class TestReadRows:
    def test_normalises_headers_and_strips_values(self):
        source = io.StringIO(" Customer Name ,Amount\n  Ana Pop , 10 \n")

        rows = list(read_rows(source))

        assert rows[0].values == {"customer_name": "Ana Pop", "amount": "10"}
        assert rows[0].line == 2

    def test_guesses_a_semicolon_separator_and_keeps_decimal_commas(self):
        source = io.StringIO("name;amount\nAna;10.000,50\nIon;2,5\n")

        assert [r.values["amount"] for r in read_rows(source)] == ["10.000,50", "2,5"]

    def test_skips_blank_lines(self):
        source = io.StringIO("name,amount\nAna,1\n\n,\nIon,2\n")

        assert [r.values["name"] for r in read_rows(source)] == ["Ana", "Ion"]

    def test_is_lazy(self):
        source = io.StringIO("name\n" + "x\n" * 1000)

        rows = read_rows(source)
        first = next(rows)

        assert first.values == {"name": "x"}  # one row read, 999 still in the file

    def test_reads_the_branch_files(self):
        iasi = list(read_file(DATA / "branch-iasi-2026-03.csv"))
        cluj = list(read_file(DATA / "branch-cluj-2026-03.csv"))

        assert len(iasi) == 9
        assert "nume_client" in cluj[0].values  # BOM gone, header normalised
        assert cluj[0].values["suma"] == "10.000,50"


class TestExport:
    def test_one_query_with_repaid_amounts_and_loans_without_repayments(self, service, session):
        first = service.open_loan("Ana Pop", "PERS", Decimal("10000.00"), 12)
        service.repay(first.id, Decimal("100.10"), "k1")
        service.repay(first.id, Decimal("0.20"), "k2")
        service.open_loan("Ion Rusu", "AUTO", Decimal("20000.00"), 24)

        rows = list(loan_report_rows(session))

        assert rows[0]["repaid"] == "100.30"
        assert rows[0]["outstanding"] == "9899.70"
        assert rows[1]["repaid"] == "0.00"
        assert rows[1]["createdOn"] == "2026-03-01"

    def test_filters_by_status(self, service, session):
        loan = service.open_loan("Ana Pop", "PERS", Decimal("1000.00"), 6)
        service.repay(loan.id, Decimal("1000.00"), "k")
        service.open_loan("Ion Rusu", "PERS", Decimal("1000.00"), 6)

        assert [r["customerName"] for r in loan_report_rows(session, status="closed")] == ["Ana Pop"]

    def test_writes_csv_with_a_header(self, service, session):
        service.open_loan("Ana Pop", "PERS", Decimal("1000.00"), 6)
        out = io.StringIO()

        count = write_csv(loan_report_rows(session), out)

        lines = out.getvalue().splitlines()
        assert count == 1
        assert lines[0] == ",".join(REPORT_COLUMNS)
        assert lines[1] == "LN-0001,Ana Pop,PERS,1000.00,0.00,1000.00,active,2026-03-01"

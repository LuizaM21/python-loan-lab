"""Reference tests, lesson 19: the new pipeline. Copy to tests/unit/test_import_pipeline.py.

Expected values worked out by hand from data/*.csv and the domain rules (see lesson 19).
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select

from loanlab.importer.extract import read_file
from loanlab.importer.pipeline import LoanImporter
from loanlab.models import Loan

DATA = Path(__file__).resolve().parents[2] / "data"


def loan_count(session) -> int:
    return session.scalar(select(func.count()).select_from(Loan))


class TestLoanImporter:
    def test_imports_the_good_rows_of_the_iasi_file_and_reports_the_rest(self, session, events):
        report = LoanImporter(session, events).run(read_file(DATA / "branch-iasi-2026-03.csv"))

        assert report.imported == ["LN-0001", "LN-0002", "LN-0003", "LN-0004", "LN-0005"]
        assert [e.line for e in report.rejected] == [6, 7, 8, 9]
        assert "duplicate" in report.rejected[0].problems[0]
        assert "Unknown loan product." in report.rejected[2].problems

    def test_cleans_the_cluj_file_and_lists_every_problem(self, session, events):
        report = LoanImporter(session, events).run(read_file(DATA / "branch-cluj-2026-03.csv"))

        assert len(report.imported) == 2
        assert [(e.line, e.problems[0].split(":")[0]) for e in report.rejected] == [
            (4, "customer_name"),
            (5, "months"),
            (6, "amount"),
        ]

    def test_uses_the_row_date_as_the_opening_date(self, session, events):
        LoanImporter(session, events).run(read_file(DATA / "branch-cluj-2026-03.csv"))

        assert session.get(Loan, 1).created_on.isoformat() == "2026-03-04"

    def test_never_commits_so_the_caller_can_do_a_dry_run(self, session, events):
        report = LoanImporter(session, events).run(read_file(DATA / "branch-iasi-2026-03.csv"))

        session.rollback()

        assert len(report.imported) == 5
        assert loan_count(session) == 0

    def test_records_an_event_for_each_imported_loan(self, session, events):
        LoanImporter(session, events).run(read_file(DATA / "branch-cluj-2026-03.csv"))

        assert events.counts_by_type() == {"loan_opened": 2}

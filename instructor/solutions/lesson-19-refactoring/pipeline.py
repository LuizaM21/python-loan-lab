"""Reference solution, lesson 19: loanlab/importer/pipeline.py — the importer after refactoring.

Extract (extract.read_rows) -> Clean (clean.clean_row) -> Load (LoanService.open_loan) -> Report.

Decisions, each one answering a smell from the legacy file:
- Rules live in ONE place, the service. The importer never builds a Loan itself. (Limits bypassed.)
- One SAVEPOINT per row: a row that fails rolls back alone; the session stays usable. (Bad date killed
  the rest of the file.)
- The importer never commits. The caller owns the transaction: commit once at the end (the file is
  all-or-nothing if the process crashes), or roll back for a dry run. (Per-row commit, half-imported files.)
- A report object, not prints and a global counter. Every rejected row keeps its line, its problems
  and its raw values, so a person can fix the file. (Silent `except: pass`.)
- Dependencies come in through the constructor (session, events); nothing is global. Easy to test.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from ..errors import LoanLabError
from ..events import EventLog
from ..models import Loan
from ..services import LoanService
from .clean import CleaningError, CleanLoanRow, clean_row
from .extract import RawRow


@dataclass(frozen=True, slots=True)
class RowError:
    line: int
    problems: tuple[str, ...]
    values: tuple[str, ...]

    def __str__(self) -> str:
        return f"line {self.line}: {'; '.join(self.problems)} [{', '.join(self.values)}]"


@dataclass
class ImportReport:
    imported: list[str] = field(default_factory=list)  # loan references
    rejected: list[RowError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.rejected


class LoanImporter:
    def __init__(self, session: Session, events: EventLog) -> None:
        self._session = session
        self._events = events

    def run(self, rows: Iterable[RawRow]) -> ImportReport:
        report = ImportReport()
        seen: set[str] = set()
        for raw in rows:
            try:
                row = clean_row(raw.values)
            except CleaningError as exc:
                report.rejected.append(self._error(raw, exc.problems))
                continue
            if row.customer_key in seen:
                report.rejected.append(self._error(raw, [f"duplicate customer {row.customer_name}"]))
                continue
            try:
                loan = self._load(row)
            except LoanLabError as exc:
                report.rejected.append(self._error(raw, [exc.message]))
                continue
            seen.add(row.customer_key)
            report.imported.append(loan.reference or "")
        return report

    def _load(self, row: CleanLoanRow) -> Loan:
        with self._session.begin_nested():  # SAVEPOINT: released on success, rolled back on error
            service = LoanService(self._session, self._events, today=lambda: row.opened_on)
            return service.open_loan(row.customer_name, row.product_code, row.amount, row.months)

    @staticmethod
    def _error(raw: RawRow, problems: Iterable[str]) -> RowError:
        return RowError(raw.line, tuple(problems), tuple(raw.values.values()))

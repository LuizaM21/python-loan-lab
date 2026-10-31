"""Reference solution, lesson 19: loanlab/legacy/loan_import.py after the refactoring.

Strangler fig: the nightly job still calls `python -m loanlab.legacy.loan_import FILE` and other code
still calls `import_file(session, path)`, so this module stays, but only as a thin adapter over the new
pipeline. When nothing calls it any more, delete it. Its lint exceptions in pyproject.toml are gone.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from loanlab.db import make_engine, make_sessionmaker
from loanlab.events import EventLog, InMemoryEventLog
from loanlab.importer.extract import read_file
from loanlab.importer.pipeline import LoanImporter
from loanlab.models import Base

logger = logging.getLogger("loanlab.import")


def import_file(
    session: Session,
    path: str | Path,
    errors: list[str] | None = None,
    events: EventLog | None = None,
) -> list[str]:
    """Same contract as before: import the file, commit, return the error messages."""
    errors = [] if errors is None else errors
    report = LoanImporter(session, events or InMemoryEventLog()).run(read_file(path))
    session.commit()
    errors.extend(str(error) for error in report.rejected)
    logger.info("import finished", extra={"fields": {"imported": len(report.imported), "rejected": len(errors)}})
    return errors


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO)
    engine = make_engine("sqlite:///loanlab.sqlite3")
    Base.metadata.create_all(engine)
    with make_sessionmaker(engine)() as session:
        problems = import_file(session, argv[1])
    for problem in problems:
        print(f"ERROR {problem}")
    return 1 if problems else 0  # a non-zero exit code lets the scheduler alert someone


if __name__ == "__main__":
    sys.exit(main(sys.argv))

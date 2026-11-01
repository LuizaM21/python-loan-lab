# Reference fix, lesson 18: loanlab/legacy/loan_import.py after the six tickets.
#
# Bug fixing, not refactoring: the shape stays the same, every change is the smallest one that removes
# a ROOT CAUSE, and each one is tied to a ticket. The structure is still poor; lesson 19 fixes that.
import csv
import sys

from loanlab.db import make_engine, make_sessionmaker
from loanlab.errors import LoanLabError
from loanlab.events import InMemoryEventLog
from loanlab.importer.clean import CleaningError, customer_key, parse_amount, parse_date
from loanlab.models import Base
from loanlab.services import LoanService

imported_count = 0


def import_file(session, path, errors=None, events=None):  # IMP-103: no shared default list
    global imported_count
    if errors is None:
        errors = []
    events = events or InMemoryEventLog()
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader)
        seen = set()
        for line, row in enumerate(reader, start=2):
            if len(row) == 0:
                continue
            try:
                name = row[0]
                key = customer_key(name)  # IMP-104: compare normalised names
                if key in seen:
                    errors.append(f"line {line}: duplicate customer {name.strip()}")
                    continue
                opened_on = parse_date(row[4])  # IMP-102: day first; IMP-106: a bad date is an error
                # IMP-105: the service owns the rules (limits, names, references, events).
                # The row's date is the service's "today": the clock is injected, not patched.
                # (d=opened_on binds the value now; a plain lambda would read the loop variable later.)
                service = LoanService(session, events, today=lambda d=opened_on: d)
                loan = service.open_loan(
                    name,
                    row[1],
                    parse_amount(row[2]),  # IMP-101: thousands separators
                    int(row[3]),
                )
                session.commit()
                seen.add(key)
                imported_count = imported_count + 1
                print("imported " + (loan.reference or "") + " " + loan.customer_name)
            except (CleaningError, LoanLabError, ValueError, IndexError) as exc:
                # IMP-101/106: never swallow; roll back so the session stays usable for the next row
                session.rollback()
                errors.append(f"line {line}: {exc} [{', '.join(row)}]")
    print("done, " + str(imported_count) + " loans, " + str(len(errors)) + " errors")
    return errors


if __name__ == "__main__":
    engine = make_engine("sqlite:///loanlab.sqlite3")
    Base.metadata.create_all(engine)
    s = make_sessionmaker(engine)()
    errs = import_file(s, sys.argv[1])
    for e in errs:
        print("ERROR " + e)

# Branch loan import. Runs every night on the files the branches upload.
# Written in 2019 by a contractor. "It works, don't touch it."
#
# Usage: python -m loanlab.legacy.loan_import data/branch-iasi-2026-03.csv
#
# LESSON 18 (bug fixing) and LESSON 19 (refactoring) work on this file.
# It is bad on purpose. Do not copy its style. pyproject.toml switches some lint rules off for this
# folder: that list is technical debt, and removing it is part of lesson 19.
import csv
import sys
from datetime import datetime
from decimal import Decimal

from loanlab.db import make_engine, make_sessionmaker
from loanlab.models import Base, Loan
from loanlab.products import _PRODUCTS

imported_count = 0


def parse_date(s):
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except:
            pass
    return None


def import_file(session, path, errors=[]):
    global imported_count
    f = open(path)
    reader = csv.reader(f)
    header = next(reader)
    seen = []
    for row in reader:
        try:
            if len(row) == 0:
                continue
            name = row[0]
            code = row[1]
            amount = float(row[2].replace(",", "."))
            months = int(row[3])
            d = parse_date(row[4])
            if name in seen:
                errors.append("duplicate customer " + name)
                continue
            seen.append(name)
            rate = None
            for p in _PRODUCTS:
                if p.code == code.upper().strip():
                    rate = p.annual_rate
            if rate == None:
                errors.append("unknown product " + code)
                continue
            r = float(rate) / 12
            payment = round(amount * r / (1 - (1 + r) ** -months), 2)
            loan = Loan(
                customer_name=name,
                product_code=code.upper().strip(),
                amount=Decimal(amount),
                annual_rate=rate,
                months=months,
                monthly_payment=Decimal(payment),
                outstanding=Decimal(amount),
                status="active",
                created_on=d,
            )
            session.add(loan)
            session.flush()
            loan.reference = "LN-" + str(loan.id).zfill(4)
            session.commit()
            imported_count = imported_count + 1
            print("imported " + loan.reference + " " + name)
        except:
            pass
    print("done, " + str(imported_count) + " loans, " + str(len(errors)) + " errors")
    return errors


if __name__ == "__main__":
    engine = make_engine("sqlite:///loanlab.sqlite3")
    Base.metadata.create_all(engine)
    s = make_sessionmaker(engine)()
    errs = import_file(s, sys.argv[1])
    for e in errs:
        print("ERROR " + e)

"""Reference, lesson 17 task 4: the same cleaning with pandas (pip install pandas).

Run from the repo root (after the clean.py exercise is done):
    python instructor/solutions/lesson-17-import-export/pandas_clean.py data/branch-cluj-2026-03.csv

The points: read everything as TEXT (dtype=str) so pandas never turns amounts into floats; reuse
the same tested parse functions for money; collect problems per row instead of dropping rows.
"""

from __future__ import annotations

import sys

import pandas as pd

from loanlab.importer.clean import CleaningError, canonical, clean_row
from loanlab.importer.extract import normalise_header


def clean_frame(path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(path, sep=None, engine="python", dtype=str, keep_default_na=False, encoding="utf-8-sig")
    raw.columns = [normalise_header(c) for c in raw.columns]
    raw = raw.apply(lambda col: col.str.strip())
    raw["line"] = raw.index + 2  # header is line 1

    good, bad = [], []
    for record in raw.to_dict("records"):
        line = record.pop("line")
        try:
            row = clean_row(record)
            good.append(
                {
                    "line": line,
                    "customer_name": row.customer_name,
                    "customer_key": row.customer_key,
                    "product_code": row.product_code,
                    "amount": row.amount,  # Decimal, object column
                    "months": row.months,
                    "opened_on": row.opened_on,
                }
            )
        except CleaningError as exc:
            bad.append({"line": line, "problems": "; ".join(exc.problems), **canonical(record)})

    clean = pd.DataFrame(good)
    if not clean.empty:
        duplicate = clean.duplicated(subset="customer_key", keep="first")
        for _, row in clean[duplicate].iterrows():
            bad.append({"line": row["line"], "problems": "duplicate customer"})
        clean = clean[~duplicate]
    return clean, pd.DataFrame(bad)


if __name__ == "__main__":
    clean, rejected = clean_frame(sys.argv[1])
    print(clean.to_string(index=False))
    print()
    print(rejected.to_string(index=False))

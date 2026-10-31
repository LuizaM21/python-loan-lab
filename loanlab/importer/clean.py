"""Clean: raw text -> typed values. Lesson 17 asks you to write these functions, test-first.

Tests: tests/exercises/test_clean.py   Run: pytest -m exercise tests/exercises/test_clean.py

Rules (from the branch offices' real files):

Names
- Trim, and collapse runs of spaces inside ("  Ana   Pop " -> "Ana Pop"). Keep the case as given.
- Empty after trimming -> CleaningError. More than 100 characters -> CleaningError.
- The DEDUPLICATION key is the cleaned name, case-folded: "ANA POP" and " ana  pop" are one customer.

Amounts (text from Excel, typed by people, in Romanian or English format)
- Allowed: "10000", "10000.50", "10000,50", "10,000.50", "10.000,50", "1 250,50", "1250 RON", "RON 1250".
- Spaces and a "RON"/"lei" label (any case) are ignored.
- If both '.' and ',' appear, the LAST one is the decimal separator; the other groups thousands.
- If only one kind appears once and is followed by exactly 3 digits, it groups thousands
  ("1,250" -> 1250, "1.250" -> 1250). Followed by 1 or 2 digits, it is the decimal separator.
- If one kind appears more than once, it groups thousands ("1.250.000" -> 1250000).
- Result: Decimal with at most 2 decimals, > 0. Anything else -> CleaningError. NEVER go via float.

Months
- Whole number, > 0: "12", " 12 ". "12.5", "twelve", "" -> CleaningError.

Dates
- ISO "2026-03-04", or day first: "04/03/2026", "04.03.2026", "4/3/2026". Never month first:
  the branches are in Romania. "2026-02-30" or "13/13/2026" -> CleaningError.

Product codes
- Trim and upper-case ("pers " -> "PERS"). Empty -> CleaningError. Whether the product EXISTS is a
  business rule: the service checks it when loading, not the cleaner.

Rows
- Headers can have different names in different branches; HEADER_ALIASES maps them.
- clean_row() collects EVERY problem in the row (not only the first) and raises one CleaningError
  listing them all, so a person fixes the file in one go.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

MAX_NAME = 100

# canonical field -> header names seen in branch files (already normalised by extract.normalise_header)
HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "customer_name": ("customer_name", "customer", "name", "nume_client", "client"),
    "product_code": ("product_code", "product", "produs"),
    "amount": ("amount", "suma", "loan_amount"),
    "months": ("months", "term", "luni", "term_months"),
    "opened_on": ("opened_on", "date", "data", "open_date"),
}


class CleaningError(ValueError):
    """A value (or a row) that cannot be cleaned. `problems` holds one message per bad field."""

    def __init__(self, problems: list[str] | str):
        self.problems = [problems] if isinstance(problems, str) else list(problems)
        super().__init__("; ".join(self.problems))


@dataclass(frozen=True, slots=True)
class CleanLoanRow:
    customer_name: str
    product_code: str
    amount: Decimal
    months: int
    opened_on: date

    @property
    def customer_key(self) -> str:
        return customer_key(self.customer_name)


def clean_name(raw: str | None) -> str:
    raise NotImplementedError  # TODO lesson 17


def customer_key(name: str) -> str:
    raise NotImplementedError  # TODO lesson 17


def parse_amount(raw: str | None) -> Decimal:
    raise NotImplementedError  # TODO lesson 17


def parse_months(raw: str | None) -> int:
    raise NotImplementedError  # TODO lesson 17


def parse_date(raw: str | None) -> date:
    raise NotImplementedError  # TODO lesson 17


def clean_product_code(raw: str | None) -> str:
    raise NotImplementedError  # TODO lesson 17


def canonical(values: dict[str, str]) -> dict[str, str]:
    """{"nume_client": "Ana"} -> {"customer_name": "Ana"}. Missing fields map to ""."""
    raise NotImplementedError  # TODO lesson 17


def clean_row(values: dict[str, str]) -> CleanLoanRow:
    raise NotImplementedError  # TODO lesson 17

"""Reference solution, lesson 17: loanlab/importer/clean.py (copy over the stub)."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

MAX_NAME = 100

HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "customer_name": ("customer_name", "customer", "name", "nume_client", "client"),
    "product_code": ("product_code", "product", "produs"),
    "amount": ("amount", "suma", "loan_amount"),
    "months": ("months", "term", "luni", "term_months"),
    "opened_on": ("opened_on", "date", "data", "open_date"),
}

_CURRENCY = re.compile(r"(?i)\b(ron|lei)\b")
_DIGITS_AND_SEPARATORS = re.compile(r"[0-9.,]+")
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y")  # day first; never %m/%d/%Y


class CleaningError(ValueError):
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
    name = " ".join((raw or "").split())
    if not name:
        raise CleaningError("Customer name is required.")
    if len(name) > MAX_NAME:
        raise CleaningError(f"Customer name is longer than {MAX_NAME} characters.")
    return name


def customer_key(name: str) -> str:
    return " ".join(name.split()).casefold()


def _thousands_ok(integer_part: str, separator: str) -> bool:
    groups = integer_part.split(separator)
    return 1 <= len(groups[0]) <= 3 and all(len(g) == 3 for g in groups[1:]) and all(g.isdigit() for g in groups)


def parse_amount(raw: str | None) -> Decimal:
    text = _CURRENCY.sub("", raw or "").replace(" ", "").replace(" ", "")
    if not _DIGITS_AND_SEPARATORS.fullmatch(text):
        raise CleaningError(f"Amount {raw!r} is not a positive number.")

    integer, fraction = text, ""
    if "." in text and "," in text:
        decimal_sep = "." if text.rfind(".") > text.rfind(",") else ","
        thousands_sep = "," if decimal_sep == "." else "."
        integer, fraction = text.rsplit(decimal_sep, 1)
        if not _thousands_ok(integer, thousands_sep):
            raise CleaningError(f"Amount {raw!r} has badly grouped thousands.")
        integer = integer.replace(thousands_sep, "")
    elif "." in text or "," in text:
        sep = "." if "." in text else ","
        if text.count(sep) > 1:
            if not _thousands_ok(text, sep):
                raise CleaningError(f"Amount {raw!r} has badly grouped thousands.")
            integer = text.replace(sep, "")
        else:
            left, right = text.split(sep)
            if len(right) == 3 and _thousands_ok(text, sep):
                integer = left + right
            elif 1 <= len(right) <= 2:
                integer, fraction = left, right
            else:
                raise CleaningError(f"Amount {raw!r} has more than 2 decimals or an unclear separator.")

    if not integer.isdigit() or (fraction and not fraction.isdigit()):
        raise CleaningError(f"Amount {raw!r} is not a number.")
    if len(fraction) > 2:
        raise CleaningError(f"Amount {raw!r} has more than 2 decimals.")
    value = Decimal(f"{integer}.{fraction or '0'}").quantize(Decimal("0.01"))
    if value <= 0:
        raise CleaningError(f"Amount {raw!r} must be more than 0.")
    return value


def parse_months(raw: str | None) -> int:
    text = (raw or "").strip()
    if not text.isdigit() or int(text) < 1:
        raise CleaningError(f"Months {raw!r} must be a whole number above 0.")
    return int(text)


def parse_date(raw: str | None) -> date:
    text = (raw or "").strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise CleaningError(f"Date {raw!r} is not YYYY-MM-DD or DD/MM/YYYY.")


def clean_product_code(raw: str | None) -> str:
    code = (raw or "").strip().upper()
    if not code:
        raise CleaningError("Product code is required.")
    return code


def canonical(values: dict[str, str]) -> dict[str, str]:
    result = {}
    for field, aliases in HEADER_ALIASES.items():
        result[field] = next((values[a] for a in aliases if a in values), "")
    return result


_PARSERS: dict[str, Callable[[str], Any]] = {
    "customer_name": clean_name,
    "product_code": clean_product_code,
    "amount": parse_amount,
    "months": parse_months,
    "opened_on": parse_date,
}


def clean_row(values: dict[str, str]) -> CleanLoanRow:
    fields = canonical(values)
    cleaned: dict[str, Any] = {}
    problems: list[str] = []
    for field, parser in _PARSERS.items():
        try:
            cleaned[field] = parser(fields[field])
        except CleaningError as exc:
            problems.extend(f"{field}: {p}" for p in exc.problems)
    if problems:
        raise CleaningError(problems)
    return CleanLoanRow(**cleaned)

"""Extract: CSV file -> raw rows. No cleaning here, no database: one job only.

Branch files differ: some use ',' and some ';' as the separator, some start with a BOM (Excel),
headers have stray spaces and capitals. We accept all of that here and keep every value as text.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


@dataclass(frozen=True, slots=True)
class RawRow:
    line: int  # line number in the file, for error reports a human can act on
    values: dict[str, str]  # header (stripped, lower case, spaces -> _) -> value (stripped)


def normalise_header(name: str) -> str:
    return "_".join(name.strip().lower().split())


def read_rows(source: TextIO, delimiter: str | None = None) -> Iterator[RawRow]:
    """Yield one RawRow per non-empty data line. Lazy: a 2 GB file never sits in memory.

    `delimiter=None` guesses between ',', ';' and TAB from the first few KB.
    """
    if delimiter is None:
        sample = source.read(4096)
        source.seek(0)
        try:
            delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
        except csv.Error:
            delimiter = ","
    reader = csv.DictReader(source, delimiter=delimiter)
    if reader.fieldnames is None:
        return
    reader.fieldnames = [normalise_header(name) for name in reader.fieldnames]
    for row in reader:
        values = {key: (value or "").strip() for key, value in row.items() if key is not None}
        if not any(values.values()):
            continue  # blank line at the end of the file
        yield RawRow(line=reader.line_num, values=values)


def read_file(path: str | Path, delimiter: str | None = None) -> Iterator[RawRow]:
    """Open with utf-8-sig (drops an Excel BOM) and newline="" (what the csv module needs).

    `with` closes the file even if the caller stops early or an exception escapes.
    """
    with open(path, encoding="utf-8-sig", newline="") as source:
        yield from read_rows(source, delimiter)

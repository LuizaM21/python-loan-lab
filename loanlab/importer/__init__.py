"""Loan import and export: Extract -> Clean -> Load, and back out again. Lessons 17-19.

- `extract.py`: read raw rows from a CSV file, lazily (a generator).
- `clean.py`: turn raw text into typed, normalised values, or say exactly what is wrong (lesson 17).
- `export.py`: extract data back out of the database for reports (streaming, one SQL query).

`loanlab/legacy/loan_import.py` is the old importer that lesson 18 debugs and lesson 19 replaces.
"""

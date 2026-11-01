# 17 — Data cleaning, loading, and extracting data back out

Time: 120 minutes.

Goal: say clearly what data cleaning is, build a cleaner for real messy files test-first, and
extract data from the database efficiently for reports.

You know this world from load testing client data migrations: messy client files, volumes, and
the question "did every record arrive, correctly?". Now you build the pipeline yourself.

## Learn: what data cleaning is

**Data cleaning** turns raw input into data that is *correct, consistent and usable*: it parses
types, normalises formats, removes or flags duplicates, and **rejects with a reason** what cannot be
trusted. It is not "make the errors go away": a good cleaner never guesses silently.

It sits in a pipeline. **ETL**: Extract (read the source) -> Transform (clean, validate, enrich) ->
Load (write to the target). **ELT** loads raw data first and transforms inside the warehouse (common
with big data tools). This lab is ETL, and then the reverse: extracting data **out** for reports.

### Data quality dimensions

| Dimension | Question | Example in `data/` |
| --- | --- | --- |
| Completeness | Is every required value there? | Cluj line 4: no customer name |
| Validity | Is it the right type and format? | `twelve` months, `2026-02-30` |
| Consistency | Is the same thing written the same way? | `pers` / `PERS`; `,` vs `;` files; `10.000,50` vs `10,000.50` |
| Uniqueness | Is each customer there once? | `Ana Pop` and `ana pop` in the Iași file |
| Accuracy / business rules | Is it allowed? | PERS of 900,000 RON (max 50,000); product `CARD` does not exist |
| Timeliness | Is it current? | None in these files. What would you check in a file called `...-2026-03.csv`? |

### What branch files really look like

Encodings and a BOM from Excel (`﻿` before the first header). Separators `,` or `;`. Headers in
English or Romanian, with spaces and capitals. Numbers in Romanian format (`10.000,50`) and English
format (`10,000.50`), with `RON` or `lei` typed in. Dates day-first, with `/` or `.`. Stray spaces
everywhere. Empty lines at the end. Duplicates that differ only in case.

### Principles

1. **Read everything as text first.** Type conversion is a cleaning step you control, not something
   a library does for you (pandas would turn `10000.50` into a float, and `03/04/2026` into a guess).
2. **Never go through `float` for money.** Text -> `Decimal`.
3. **Separate parsing from business rules.** The cleaner knows formats ("is this a date?"). The
   service knows rules ("is 900,000 allowed for PERS?"). Rules must not be duplicated in the importer.
4. **Never drop a row silently.** Every rejected row is reported with its **line number**, **every**
   problem in it, and its raw values, so a person can fix the file in one go.
5. **Ambiguity is an error, not a guess.** Is `1,250` one thousand two hundred fifty or one point
   two five? Define the rule (3 digits after one separator = thousands) and test it.
6. **Keep the raw input.** Store the original file; you will need it for the next bug.
7. **Make the load idempotent.** Importing the same file twice must not create duplicates
   (dedupe keys, a file checksum table, or upserts).
8. **Stream.** Generators and batched queries keep memory flat for any file size.

## Learn: extracting data back out

Reports and exports are the other direction. `loanlab/importer/export.py` shows the rules:

- **One query**, not one per row: "repaid so far" is a `SUM` per loan in a subquery, joined with a
  `LEFT OUTER JOIN` so loans without repayments still appear (with 0).
- **Select columns, not ORM objects**: no identity map, no change tracking, much less memory.
- **Stream**: `yield_per(500)` fetches in batches, and the function is a generator, so the first CSV
  line goes out before the last row is read. For millions of rows in PostgreSQL: server-side cursors,
  or `COPY ... TO STDOUT`.
- **Format at the edge**: money as strings with 2 decimals, dates as ISO 8601.
- **Same filters as the API** (status), so numbers in the report match the screen.

### pandas, briefly

Interviewers may ask about pandas. The equivalents, and the traps:

| Step | pandas | Trap |
| --- | --- | --- |
| Read | `pd.read_csv(path, sep=None, engine="python", dtype=str, keep_default_na=False, encoding="utf-8-sig")` | Without `dtype=str`, amounts become floats and leading zeros vanish |
| Trim | `df[col].str.strip()` | |
| Normalise | `df[col].str.casefold()`, `str.replace` | |
| Dates | `pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")` | `dayfirst=True` is a hint, not a rule; `errors="coerce"` turns bad dates into NaT **silently**: count them |
| Numbers | `pd.to_numeric(s, errors="coerce")` | Floats, and silent NaN. For money, apply your own Decimal parser |
| Duplicates | `df.duplicated(subset="customer_key", keep="first")` | |
| Missing | `df.isna().sum()` | |

pandas is great for exploring a file and for analytics. For a production importer of money, a
small tested pipeline with explicit rules is easier to trust.

## In this repo

| File | Shows |
| --- | --- |
| `data/branch-iasi-2026-03.csv`, `data/branch-cluj-2026-03.csv` | Two real-looking messy files (synthetic data) |
| `loanlab/importer/extract.py` | Extract: separator guessing, BOM, header normalisation, generator |
| `loanlab/importer/clean.py` | The rules for cleaning, as a stub: your exercise |
| `loanlab/importer/export.py` | Extract back out: one query, outer join + SUM, streaming, CSV |
| `loanlab/legacy/loan_import.py` | How not to do it (lessons 18 and 19) |

## Do

### 1. Profile the data before writing code

Open both files in a text editor (not Excel: it changes them). In `notes/data-profile.md`, list
every problem per line, and which quality dimension it is. Count: how many rows should import from
each file, and why? (Hint: check every row against the domain rules in `CLAUDE.md` too.) Keep the
list: lesson 19 uses your counts as expected values.

### 2. Exercise: the cleaner, test-first

`loanlab/importer/clean.py` states the rules; `tests/exercises/test_clean.py` has the tests. Work in
this order, one group at a time, red then green: names, months, product codes, dates, amounts (the
hardest), `canonical`, `clean_row`. Run `pytest -m exercise tests/exercises/test_clean.py`.

For `parse_amount`, write the decision table first, in your notes:
both `.` and `,` present / only one kind, once / only one kind, several times; then digits after the
last separator: 1–2, exactly 3, other. Every cell is a test case. When green, add 3 cases of your own.

### 3. Export

Write `notes/export_report.py`: build an app with `DEMO_LOANS=200` (or open loans with the service),
then `write_csv(loan_report_rows(session, status="active"), sys.stdout)`. Check one row by hand:
`amount - repaid == outstanding`. Then count queries (your lesson 04 helper): how many for 200
loans? How many would a loop with `loan.repayments` need?

### 4. Optional: the same in pandas

`pip install pandas`. Read the Cluj file with `dtype=str`, clean it by applying your `clean_row` per
row, and find duplicates with `duplicated()`. Then try `pd.read_csv` **without** `dtype=str` and look
at `df.dtypes` and the amounts. What went wrong?

## Check yourself

1. What is data cleaning? What is it not?
2. ETL vs ELT.
3. Name five data quality dimensions with an example of each.
4. Why read everything as text first? Why never float for money?
5. Where does "PERS max 50,000.00" belong: the cleaner or the service? Why?
6. Why report every problem in a row, with the line number?
7. How do you make an import idempotent?
8. How do you export a million rows without running out of memory?
9. One pandas trap with dates and one with numbers.

## Say it in the interview

- "Data cleaning means turning raw input into typed, consistent data, and rejecting with a reason
  what can't be trusted. I never guess silently: every rejected row comes back with its line
  number and every problem in it."
- "I read files as text and parse money straight to Decimal. Format parsing lives in the cleaner;
  business limits live in the service, so the importer and the API can't disagree."
- "For exports I select columns, aggregate in SQL and stream with a generator and `yield_per`. One
  query, flat memory, and the first line goes out immediately."
- "I tested client data migrations under load at Mambu, so I know the other side: volumes, and the
  question 'did every record arrive correctly?'. That's why my importer always reconciles: rows
  read = imported + rejected."

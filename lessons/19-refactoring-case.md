# 19 — A case for refactoring: why, then how

Time: 150 minutes.

Goal: make the business case for a refactoring that a product owner would accept, then do it in
small, safe, green steps, ending with the legacy importer replaced by a clean pipeline.

**Refactoring** = changing the structure of code **without changing its behaviour**, in small steps,
with tests green after each one. A rewrite is not a refactoring. A bug fix is not a refactoring.

## Learn: the WHY — making the case

Nobody approves "the code is ugly". They approve less risk, less cost, more speed. Make the case
with evidence from the code and from the tickets.

### The evidence in `loanlab/legacy/loan_import.py`

| Smell | Where | Cost it causes |
| --- | --- | --- |
| Long function, many jobs (reads, parses, validates, calculates, saves, commits, prints) | `import_file` | Every change risks every other job; impossible to test one part |
| Silent `except: pass` | the row loop, `parse_date` | Data loss with no error (IMP-101, IMP-106) |
| Business rules duplicated, and incomplete | its own product lookup and payment maths | Loans outside limits (IMP-105); two places to change for every rule change |
| `float` for money | `float(row[2]...)`, `round(...)` | Correct today by luck of magnitude; a rounding incident waiting to happen |
| Module-level mutable state | `imported_count`, `errors=[]` | Results depend on history of the process (IMP-103) |
| Magic indexes | `row[0]`, `row[4]` | A new column in the file shifts everything silently |
| Resource leak, platform default encoding | `open(path)` without `with` / `encoding` | File handles leak in a long-running worker; non-ASCII names break on another OS |
| Commit per row | `session.commit()` in the loop | A crash leaves half a file imported; re-running creates duplicates |
| Reaches into private names | `from loanlab.products import _PRODUCTS` | Internal changes in `products.py` break the importer |
| Hard-coded wiring | database URL in `__main__` | Can't run against staging, can't test the CLI |
| `print` instead of logging | everywhere | No levels, no request/job id, nothing for alerts |
| Lint exceptions | `pyproject.toml` per-file-ignores | The tools are switched off exactly where they're needed |
| No tests (until lesson 18) | | Every change is a gamble |

### The business case, one page

Write it in `notes/refactoring-case.md` for the product owner, in their terms:

1. **Problem**: 6 tickets in one month from one 90-line file, two of them silent data loss and one a
   risk breach (IMP-105). Each fix took N hours because nothing was tested and everything is coupled.
2. **Risk if we don't**: the next format change from a branch (a new column, a new date format)
   will cause another silent loss. Point to the magic indexes and the `except: pass`.
3. **Proposal**: replace the internals with a tested Extract -> Clean -> Load pipeline that uses the
   same rules as the API. Keep the command line and the `import_file` function, so the nightly job
   and its callers don't change.
4. **Cost and safety**: about 2 days, in 10 small steps, each one green and releasable. Tests from
   the bug fixes guard the behaviour. Rollback = revert one commit.
5. **What gets better, measurably**: every rejected row reported with a reason (no silent loss);
   rules in one place; whole-file atomic import; a dry-run mode; lint and type checks back on.
6. **What we don't do**: no new features, no change to file formats, no change to the database.

### When not to refactor

Code that works and **doesn't change**; code about to be deleted; no tests and no time to write
them (write the characterization tests first, or don't touch it); in the middle of an incident
(mitigate first). Refactor the code you're working in, when you're working in it.

## Learn: the HOW — small safe steps

Preconditions: the characterization and ticket tests from lesson 18 are green and committed.

Rules: one small step at a time; run the tests after every step; commit after every green step
(`refactor: ...`); never mix a behaviour change into a refactoring commit; if a step goes red and
the fix isn't obvious, `git checkout .` and take a smaller step.

| Technique | Name in Fowler's catalogue |
| --- | --- |
| Pull a block out into a named function | Extract Function |
| Replace `row[0]` with named fields | Replace Primitive with Object / use `csv.DictReader` |
| Group loose values into a dataclass | Introduce Parameter Object (`CleanLoanRow`) |
| Pass dependencies in instead of creating them | Dependency injection, "Parameterize Function" |
| Replace a global with a returned value | Replace Global with Return Value (`ImportReport`) |
| Delete the duplicate rule, call the real one | Substitute Algorithm, "Remove Duplication" |
| Keep the old entry point, route it to new code | **Strangler Fig** |
| Hide the old and new behind one interface, switch, delete the old | Branch by Abstraction |

### The target design

```
read_file(path) ──> RawRow(line, values) ──> clean_row(values) ──> LoanService.open_loan(...)
  (extract.py)        lazily, one at a time     (clean.py, lesson 17)   (the ONE place for rules)
                                     │                                        │
                                     └──── rejected: RowError(line, problems, raw values) ────> ImportReport
```

`LoanImporter(session, events).run(rows) -> ImportReport` in `loanlab/importer/pipeline.py`:

- cleans each row with `clean_row`; a `CleaningError` becomes a `RowError` with **all** problems;
- skips a duplicate customer (by `customer_key`) with a `RowError`;
- opens the loan through `LoanService`, with the row's date as the service's `today`;
- puts each row's load in a **SAVEPOINT** (`session.begin_nested()`): a failing row rolls back alone;
- **never commits**: the caller commits once (atomic file) or rolls back (dry run);
- returns `ImportReport(imported=[references], rejected=[RowError])`.

`loanlab/legacy/loan_import.py` keeps `import_file(session, path, errors=None, events=None)` and the
command line, as a thin adapter: run the pipeline, commit, return the error messages. Exit code 1 if
any row was rejected, so the scheduler can alert.

### The steps

Each step: change, run `pytest`, commit.

1. Add `with open(path, encoding="utf-8-sig", newline="")`. (Behaviour: same, minus the leak.)
2. Replace `csv.reader` + `row[0]` with `read_file(path)` and `raw.values` + `canonical(...)`.
3. Replace the hand-written parsing with `clean_row(raw.values)`; the `CleaningError` problems go
   to `errors`.
4. Delete the product lookup and payment maths; call `LoanService.open_loan`. (Lesson 18 may have
   done part of this.)
5. Replace the commit per row with `begin_nested()` per row, and one commit at the end in
   `import_file`. Add a test: "the importer never commits" (roll back after `run`, nothing saved).
6. Introduce `RowError` and `ImportReport`; `import_file` formats the report into the old error list.
7. Move the loop into `LoanImporter.run(rows)` in `loanlab/importer/pipeline.py`. `import_file`
   becomes three lines.
8. Delete `imported_count` and the `print`s; log one summary line with counts.
9. Make the CLI a `main(argv) -> int` with an exit code, and test it.
10. Remove the `loanlab/legacy/loan_import.py` entry from `per-file-ignores` in `pyproject.toml`;
    `ruff check .` and `mypy` must pass. Add type hints to `import_file`.

## In this repo

| File | Shows |
| --- | --- |
| `loanlab/legacy/loan_import.py` | The before |
| `tests/unit/test_legacy_import.py` | Your safety net from lesson 18 |
| `loanlab/importer/extract.py`, `clean.py` | The building blocks |
| `pyproject.toml` | `per-file-ignores`: the debt to pay off in step 10 |

## Do

### 1. Write the case

`notes/refactoring-case.md`, one page, using the template above and **your** numbers: how long did
lesson 18 take you? How many places would a new date format touch today?

### 2. Do the ten steps

Use a branch `refactor/importer` and one commit per step. If a characterization test goes red during
a refactoring step, you changed behaviour: stop, find out why.

### 3. Tests for the pipeline

In `tests/unit/test_import_pipeline.py`, using `read_file` on the two files in `data/`, with your
counts from lesson 17 (task 1) as expected values, **worked out by hand**:

- the Iași file: which references are imported, which line numbers are rejected and why;
- the Cluj file: which rows are rejected, and the **field** of the first problem of each;
- the opening date comes from the row;
- the importer never commits (roll back after `run`: no loans);
- one `loan_opened` event per imported loan.

### 4. Measure

Before and after: lines in `import_file`; number of things it does; `ruff` and `mypy` exceptions;
and if you have it, `pip install radon` then `radon cc -s loanlab/legacy loanlab/importer` for
cyclomatic complexity. Put the numbers in your case document: "after" is part of the story you tell.

## Check yourself

1. Define refactoring. How is it different from a rewrite and from a bug fix?
2. Make the case for this refactoring in four sentences a product owner would accept.
3. Name six smells in the legacy importer and the cost of each.
4. Why must the tests exist before you start? Which tests protect you here?
5. What is the Strangler Fig pattern? Why keep `import_file` at all?
6. Why a SAVEPOINT per row and one commit per file? What are the alternatives and their trade-offs?
7. When would you NOT refactor?
8. How do you show the refactoring was worth it, after?

## Say it in the interview

- "I make the case in business terms: one 90-line file caused six tickets in a month, two of them
  silent data loss. The refactoring costs two days in ten releasable steps, and the tests from the
  bug fixes guard the behaviour."
- "I don't rewrite. I keep the old entry point and move its insides to a tested pipeline step by
  step, strangler-fig style, committing after every green step."
- "The design: extract, clean and load are separate; the business rules are only in the service;
  each row loads in a savepoint; the caller commits once, so a file is all-or-nothing and a dry run
  is just a rollback."

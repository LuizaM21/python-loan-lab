# 18 — Bug fixing: from a ticket to a regression test

Time: 120 minutes.

Goal: fix bugs the way a senior does: reproduce, prove with a failing test, find the root cause,
make the smallest safe fix, and leave a regression test behind.

You will fix six real tickets in the legacy importer. Do this lesson **before** lesson 19: the tests
you write here are the safety net for the refactoring.

## Learn: the method

1. **Reproduce.** Get the input (the file, the request, the log line with the request id) and the
   exact steps. No reproduction, no fix: you would be guessing.
2. **Minimise.** Cut the input down to the smallest thing that still fails: one CSV row, one call.
3. **Write a failing test** at the lowest level that shows the bug. See it fail **for the right
   reason** (read the assertion message).
4. **Find the root cause**, not the symptom. Read the code path. Ask "why?" until the answer is code,
   not behaviour (the "5 whys").
5. **Fix the root cause with the smallest safe change.** A bug fix is not a refactoring: don't
   restructure while fixing (lesson 19 does that, with these tests in place).
6. **Run the whole suite.** Then look for **siblings**: the same mistake elsewhere.
7. **Commit** with the ticket id and the root cause: `fix(import): IMP-102 read dates day-first`.
   The PR says: symptom, root cause, fix, test.

Before step 3, classify the failure: product bug, test bug, environment, or flaky?
(`.claude/skills/triage-test-failure` describes this.)

### Tools

| Tool | Use |
| --- | --- |
| `breakpoint()` | Stops in `pdb` at that line. `n` next, `s` step in, `c` continue, `p expr` print, `pp`, `l` list, `w` where, `u`/`d` up/down the stack |
| `pytest -x --pdb` | Stop at the first failure and open the debugger there |
| `pytest --lf -x`, `-k name`, `-vv`, `-s` | Rerun last failed; one test; full diffs; show prints |
| `logging` with context | Better than `print`: levels, timestamps, request ids, stays in the code |
| `git bisect run pytest tests/unit/test_x.py -x` | Find the commit that introduced a bug automatically |
| `git log -p -- file`, `git blame` | When and why did this line change? |
| PyCharm debugger | Conditional breakpoints, "evaluate expression" |

### Python bug classes to suspect first

| Bug | Symptom |
| --- | --- |
| Bare `except:` / `except Exception: pass` | Data silently missing, "no errors" |
| Mutable default argument | State leaks between calls (only in long-running processes!) |
| Late-binding closure in a loop | All callbacks use the last value |
| `float` for money | Off by a cent, sometimes |
| Ambiguous formats (dates, decimals) | Wrong values that look valid |
| Naive vs aware datetimes, time zones | Off by hours around midnight / DST |
| Session not rolled back after a DB error | `PendingRollbackError` on everything after it |
| Comparing un-normalised strings | Duplicates that "aren't" (`"Ana Pop"` vs `" ana pop"`) |
| Validation duplicated (or skipped) outside the service | One path enforces a rule, another doesn't |
| Encoding default (`open()` without `encoding=`) | Works on your Mac, breaks on Windows or the server |
| Iterator used twice | Second pass is empty |
| Mutating a list while iterating it | Items skipped |

## Learn: the tickets

The nightly job runs `python -m loanlab.legacy.loan_import <file>` in one long-running worker
process that imports one file per branch. These are the tickets, as reported. They describe
**symptoms**; finding the cause is your job.

> **IMP-101** (Operations, Iași branch): "Elena Matei's loan is not in the system. The branch
> uploaded it on the 3rd and the import log shows no errors for it. Her row has amount `1,250.50`."

> **IMP-102** (Customer support): "Customer says her loan started on 3 April, our system says
> 4 March. Branch file row: `...,03/04/2026`."

> **IMP-103** (Operations): "Tuesday's error report lists `unknown product CARD`, but Tuesday's
> file has no CARD rows. That error was in Monday's file. Restarting the worker makes it go away."

> **IMP-104** (Risk): "Ana Pop has two loans opened on the same day from the same file. The second
> row is written `ana pop`. Duplicates are supposed to be rejected."

> **IMP-105** (Risk, priority high): "A PERS loan of 900,000 RON was imported. PERS max is 50,000."

> **IMP-106** (Operations): "On the 10th, every row after Vlad Dumitru's is missing, and the job
> crashed at the next step with `PendingRollbackError`. His row has date `2026-02-30`."

## In this repo

| File | Shows |
| --- | --- |
| `loanlab/legacy/loan_import.py` | The code with the bugs |
| `data/branch-iasi-2026-03.csv` | Rows that trigger several tickets |
| `loanlab/importer/clean.py` | Your lesson 17 work: good parsers you may reuse in a fix |
| `.claude/skills/triage-test-failure` | Classifying a failure before fixing |

## Do

All tests in `tests/unit/test_legacy_import.py`. Use pytest's `tmp_path` fixture to write small CSV
files, and the `session` fixture. Call `import_file(session, path)`.

### 1. Characterization tests first

Before touching the code, pin what it **already does right**, so your fixes can't break it:
a plain row imports with reference `LN-0001`, the right amount, `monthly_payment` `878.69` for
10,000.00 PERS over 12 months, status `active`, and the date from the file; a lower-case product
code works; an unknown product is reported in the error list; `10000,50` imports as `10000.50`.
These pass now. Commit: `test: characterize the legacy importer`.

### 2. One ticket at a time

For each ticket, in this order: 105, 106, 101, 102, 104, 103 (most harmful first):

1. Write the failing test from the **symptom** in the ticket. Run it. Read the failure.
2. Find the root cause. Write it in one sentence in the test's docstring or the commit message.
3. Smallest fix. Run the whole suite. Commit: `fix(import): IMP-105 ...`.

Hints, only if stuck for 15 minutes:

- 105: where are the product limits checked in the rest of the app? Is that code called here?
- 106: what state is a SQLAlchemy session in after a failed flush? What does `except: pass` do with
  that? And what does `parse_date` return for an impossible date?
- 101: what does `"1,250.50".replace(",", ".")` give? And where does the exception go?
- 103: run the import twice in one test. Which variable survives between calls?
- 104 and 106 interact: when a row fails, should its name count as "seen"?

### 3. Look for siblings

After the six fixes: search the file for other places with the same root causes (other bare
`except`, other `open()` without `with` and `encoding`, other module-level state). List them in
your notes; don't fix them yet. They are the case for lesson 19.

### 4. Hidden-bug drill

`instructor/bug.sh random 2`, then hunt them with new tests, as in lessons 04 and 08. Time-box 30
minutes. Use the method above and write the root cause for each.

## Check yourself

1. Your steps from a bug report to a merged fix.
2. Why write the failing test before the fix? Why must you see it fail?
3. Symptom vs root cause, with IMP-101 as the example.
4. Bug fix vs refactoring: why keep them in separate commits?
5. What is a characterization test, and why write it first here?
6. How does `git bisect run` work?
7. Why did IMP-103 only show up in production, never on a developer's machine?
8. Five Python bug classes you check first when data goes missing.

## Say it in the interview

- "First I reproduce it and cut it down to one input. Then a failing test from the symptom, then
  the root cause, then the smallest fix. The test stays as a regression test."
- "Example: rows with `1,250.50` disappeared without an error. The symptom was missing data; the
  root causes were a naive amount parser and a bare `except: pass` that swallowed the error. I fixed
  the parsing and made every rejected row show up in the error report with its line number."
- "I keep bug fixes and refactoring apart. The fix is small and easy to review; once the tests are
  in place, the refactoring is a separate, safe change."

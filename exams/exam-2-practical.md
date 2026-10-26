# Exam 2 — Practical: fix and build

Time: 90 minutes.

Your mentor has turned on **3 hidden bugs**, in different layers of the app, and gives you
**1 small ticket** (a feature). The sample tests still pass.

## Setup (your mentor does this)

Your mentor gives you a branch, for example `exam-2`. Then:

```bash
git fetch
git switch exam-2
```

Restart the API. Do not read `instructor/`, `git diff` or `git log -p`.

## Part 1 — The bugs (3 × 10 points)

For each bug:

1. **A failing test** that proves the bug, at the **lowest level** that can see it (unit, API, or
   a query-count / k6 check for speed).
2. **The fix**, as small as possible. The test now passes. All other tests still pass.
3. **A note** in `notes/exam-2.md`: title, area, severity, expected, actual, the test name, and one
   sentence on why this test level.

| Points | For |
| --- | --- |
| 4 | A test that fails because of the bug, and passes after the fix |
| 2 | The test is at the lowest level that can see the bug |
| 3 | A correct, minimal fix with nothing else broken |
| 1 | A clear note |

## Part 2 — The ticket (10 points)

Your mentor gives you one ticket, for example:

- "`GET /api/loans/<id>/summary`: amount, total repaid, outstanding, number of repayments,
  percentage repaid (2 decimals). 404 for unknown loans."
- "`GET /api/loans?productCode=AUTO`: filter by product, combined with `status` and paging; an unknown product is 400."
- "`GET /api/stats/products`: per product, the number of loans and their total amount, in one query."

| Points | For |
| --- | --- |
| 4 | It works, through the API |
| 3 | Tests written first (show the red commit), covering rules and edge cases |
| 2 | Right layer: rules in the service, a thin view |
| 1 | Clean commit messages |

Minus 2 points for each "bug" you report that is not a bug, and for each test that fails on
correct code.

## At the end

Commit your tests, fixes and notes on the branch and push. Your mentor runs the reference tests
against your branch.

## Tips

- Start with your existing tests from lessons 02–04: `pytest`. Then boundaries, status codes,
  headers, idempotency, filters and totals, then speed with many loans.
- Time-box: about 15 minutes per bug, 30 for the ticket. If one is stuck, move on.
- Small commits: `test: prove ...`, `fix: ...`, `feat: ...`.

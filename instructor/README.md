# Instructor kit

For the mentor only. The student must not open this folder.

## What is here

| Path | What |
| --- | --- |
| `bug.sh` | Turns hidden bugs on and off (`random N`, `on NN`, `off NN`, `list`, `reset`) |
| `verify.sh` | Checks every bug is hidden from the sample tests and caught by the reference tests |
| `bugs/NN.patch` | The hidden bugs, as git patches |
| `solutions/tests/` | Reference test suite. Green on correct code, red for every bug. |
| `solutions/lesson-02-totals/` | Feature patch + tests: totals on the quote |
| `solutions/lesson-03-repayments-endpoint/` | Feature patch + tests: `GET /api/loans/<id>/repayments` |
| `solutions/lesson-04-customer-search/` | Feature patch + tests: `?customer=` search and index |
| `solutions/lesson-05-django/` | Django views, admin and tests |
| `solutions/lesson-06-mongo/` | `MongoEventLog` and the contract test |
| `solutions/lesson-07-fast-stats/` | Fast `stats.py` and its characterization + query-count tests |
| `solutions/katas/` | Kata solutions |
| `answer-keys/` | Keys for the three exams and the lesson 09 review |

Apply a feature solution to look at it: `git apply instructor/solutions/lesson-03-repayments-endpoint/feature.patch`
(undo with `git apply -R ...`).

## The hidden bugs

Each bug keeps the 3 sample tests green. The level is the lowest test level that can see it.

| Bug | Layer | What is wrong | Found by |
| --- | --- | --- | --- |
| 01 | Service rules | The maximum amount of a product is rejected (`>=` instead of `>`) | Unit: boundary on the max (50,000.00 PERS) |
| 02 | Service rules | The minimum term of a product is rejected (`<=` instead of `<`) | Unit: boundary on the min (6 months PERS) |
| 03 | API contract | A retried repayment returns 201 instead of 200 | API: same idempotency key twice, check status codes |
| 04 | API security | A request **without** `X-Api-Key` is accepted (a wrong key is still rejected) | API: no header at all -> 401 and nothing saved |
| 05 | Service rules | Same idempotency key with a **different amount** returns the first repayment instead of 409 | Unit: key reuse with another amount |
| 06 | Service rules | Paying **exactly** the outstanding balance is rejected, so a loan can never close | Unit: repay the full outstanding -> closed |
| 07 | Data / ORM | `total` in the loan list ignores the `status` filter | Unit or API: `status=closed` total vs items |
| 08 | Performance | The list endpoint refreshes every loan: one extra query per row (N+1) | Query-count test with 100+ loans, or k6 p95 with `DEMO_LOANS` |

Bugs 01, 02, 05, 06 and 07 are in `loanlab/services.py`; 03 and 08 in `loanlab/api/routes.py`;
04 in `loanlab/api/auth.py`. All 8 can be on together.

## Practice bug hunts (lessons 04 and 08)

The student runs `instructor/bug.sh random 1` (then 2) alone. Nothing to do for you, except
review their tests and fixes afterwards.

## Exam 2 setup

```bash
git switch -c exam-2
instructor/bug.sh random 3          # or choose: instructor/bug.sh on 01 04 08
instructor/bug.sh list              # note which ones; do not tell the student
git add -A && git commit -m "Exam 2"
rm instructor/.active-bugs          # so `bug.sh list` shows nothing on the student's machine
git push -u origin exam-2
```

Pick bugs from different layers, for example one service rule (01, 02, 05, 06), one API or
security (03, 04), and 07 or 08. Give one ticket from `exams/exam-2-practical.md` (or your own).

Grading:

1. On the student's branch, run their tests: the bug-proving tests should be green after their fixes.
2. Check their fixes against the patches in `bugs/` (a fix may differ, but must restore the rule).
3. Run the reference suite on their branch: `pytest instructor/solutions/tests`. It must be green.
4. Score the ticket with the table in the exam and `answer-keys/exam-2-practical-key.md`.

## After you change the app

Run `instructor/verify.sh`. It must end with `VERIFIED`. If a bug patch no longer applies,
regenerate it: make the bug by hand, `git diff -- <file> > instructor/bugs/NN.patch`, then
`git checkout -- <file>`.

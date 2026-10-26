# Loan lab — agent context

A practice app for Python backend development. Flask + SQLAlchemy API (`loanlab/`), a Django
version (`django_lab/`), tests in `tests/`. Default database: SQLite, reset on every start.

## Rules

- Do not read or use anything in `instructor/`. It holds solutions, exam answers and hidden bugs.
- Work test-first: write a failing test from the **rule**, see it fail, then change the code.
- Expected values come from the Domain rules below, worked out by hand. Never copy them from the
  current output.
- Keep views thin: rules live in `loanlab/services.py`. The service never commits; the request does.
- Money is `Decimal`, never `float`. JSON carries money as strings with 2 decimals.
- Run `ruff check .`, `ruff format .`, `mypy` and `pytest` before you say a task is done.
- Use synthetic data only.

## Commands

| Task | Command | Folder |
| --- | --- | --- |
| Tests | `pytest` | repo root |
| One test | `pytest -k <name> -x` | repo root |
| Katas | `pytest -m kata` | repo root |
| Lint / format / types | `ruff check .` / `ruff format .` / `mypy` | repo root |
| Start API (port 5080) | `flask --app loanlab.api run --port 5080` | repo root |
| Django tests | `python manage.py test lending` | `django_lab` |
| k6 smoke | `k6 run perf/smoke.js` | repo root (API running) |

## Conventions

- pytest. Test classes `Test{Subject}`; method names read as a sentence
  (`test_rejects_one_cent_more_than_outstanding`). Body has `# setup`, `# execute`, `# verify`,
  each followed by one empty line.
- Unit tests: `tests/unit/`, with the `service` fixture (fresh in-memory DB, fixed date 2026-03-01).
- API tests: `tests/api/`, with the module-scoped `client` fixture. The app is shared inside a
  module: never assert exact list counts; use unique customer names.
- `parametrize` for boundaries and equivalence classes.
- Commits: Conventional Commits (`feat:`, `fix:`, `test:`, `refactor:`), small.

## Domain rules

- Products (fictional): PERS Flexi Personal 9.90%, 1,000.00–50,000.00 RON, 6–60 months;
  AUTO Auto Plus 7.50%, 5,000.00–150,000.00 RON, 12–84 months; HOME Home Start 5.50%,
  20,000.00–500,000.00 RON, 60–360 months. Limits inclusive. Product codes are case-insensitive.
- Amounts have at most 2 decimals. Customer name: trimmed, required, at most 100 characters.
- Monthly rate r = annual / 12. Payment = amount × r / (1 − (1 + r)^−months), rounded half-up to
  0.01. Each month: interest = balance × r rounded half-up; principal = payment − interest. The
  last month repays the rest, so the final balance is 0.00.
- Writes (`POST /api/loans`, `POST /api/loans/<id>/repayments`) need `X-Api-Key: lab-dev-key`,
  else 401. Success is 201 with a `Location` header for loans.
- References are `LN-0001`, `LN-0002`, … and unique.
- Repayment: amount > 0 and ≤ outstanding; exactly the outstanding closes the loan; more is 409;
  a closed loan rejects repayments (409). `Idempotency-Key` header required (1–64 characters):
  the same key + same loan + same amount returns the first repayment with 200 and charges
  nothing; the same key with a different loan or amount is 409.
- Errors are JSON `{"code": "...", "message": "..."}`: 400 invalid, 401, 404, 409.

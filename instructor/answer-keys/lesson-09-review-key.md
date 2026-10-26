# Lesson 09 — Review of PR #42, key

At least 10 of these, each with why and a fix:

| # | Problem | Why it matters | Fix | Must fix? |
| --- | --- | --- | --- | --- |
| 1 | SQL built with an f-string from the URL (`'{reference}'`) | SQL injection | Use the ORM (`select(Loan).where(Loan.reference == reference)`) or bound parameters | Must |
| 2 | `float` for money (`float(loan.outstanding)`, `0.01`) | Rounding errors on money | `Decimal` everywhere, `to_money` with HALF_UP | Must |
| 3 | `round(total, 2)` | Banker's rounding on floats; not the project's rule | `to_money()` | Must |
| 4 | Bare `except:` returning 0 | Hides every bug, tells the customer they owe 0 | Remove; let errors reach the error handler | Must |
| 5 | `self._session.commit()` in the service | Breaks the unit-of-work rule; commits half-finished request work | Never commit in the service | Must |
| 6 | Changes `status` to `"payoff_quoted"` on a GET | A read with a side effect; invalid status breaks filters and repayments | A quote must not change data | Must |
| 7 | Mutable default `extra_fees=[]`, and it appends to it | Shared state across calls: grows forever | `extra_fees: list[Decimal] | None = None`, don't mutate | Must |
| 8 | `datetime.now()` instead of the injected `today` | Untestable, timezone-dependent | Use `self._today()` | Must |
| 9 | `row.id` when the reference is unknown -> `AttributeError` -> 500 | Unknown loan should be 404 | Look up by reference in the service and raise `NotFound` | Must |
| 10 | Logs the customer name and query string at INFO | Personal data in logs (GDPR) | Log the reference and request id only | Must |
| 11 | No tests ("tested manually with Postman") | No proof, no regression protection | Unit tests for the maths with hand-worked values, API tests for 200/404 | Must |
| 12 | Interest uses `/ 365` days since creation and ignores repayments made since | Wrong amount; the rule isn't specified | Ask the product owner for the rule first; write it in the ticket | Must (clarify) |
| 13 | Response puts a float in JSON | Inconsistent with the API (money as strings) | `format_money()` | Must |
| 14 | `EARLY_PAYOFF_FEE` as a float class attribute; magic number | Precision and config | `Decimal("0.01")`, product-level config | Nit/should |
| 15 | Route uses `<reference>` while every other route uses `<int:loan_id>` | Inconsistent API | Use the id, or add reference lookup consistently | Should |
| 16 | `log = logging.getLogger(__name__)` mid-file; unused `request.args` | Style | Move to the top; the linter would flag it | Nit |
| 17 | `service()` called twice -> two service objects | Harmless here, confusing | One `svc = service()` | Nit |

A good review also asks for: tests of the fee maths with hand-worked numbers, a 404 test, a test
that a quote changes nothing in the database, and a decision from the product owner on the
interest rule.

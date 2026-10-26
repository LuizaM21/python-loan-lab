---
name: implement-feature
description: Implements a feature or change in the Loan lab API test-first (TDD), in the right layer, with lint, types and tests green. Use when asked to add or change an endpoint, a rule, or a query in loanlab/.
---

# Implement a feature test-first

1. **Find the rule.** Read the request, `CLAUDE.md` (Domain rules) and the code it touches. Write
   the rule in one or two sentences. If something is ambiguous (rounding, status code, ordering),
   stop and ask instead of guessing.
2. **Plan the layers.** Rules go in `loanlab/services.py` (or a pure module like `schedule.py`);
   request parsing and JSON in `loanlab/api/`; schema in `loanlab/models.py`. Views stay thin.
3. **Choose the cases** with test design: boundaries on and next to each limit at 0.01 precision,
   one value per equivalence class, invalid input, not found, side effects (a rejected write saves
   nothing), and the HTTP contract (status code, headers, JSON shape).
4. **Work out expected values by hand** from the rule. Never copy them from running the code.
5. **Red.** Write the lowest-level tests first (unit in `tests/unit/`, using the `service`
   fixture), then one or two API tests in `tests/api/` (module-scoped `client`, unique names, no
   exact list counts). Layout:
   ```python
   def test_rejects_one_cent_more_than_outstanding(self, service):
       # setup

       loan = service.open_loan("Ana Pop", "PERS", Decimal("1000.00"), 12)

       # execute

       with pytest.raises(Conflict) as error:
           service.repay(loan.id, Decimal("1000.01"), "k1")

       # verify

       assert error.value.message == "Repayment exceeds the outstanding balance of 1000.00 RON."
   ```
   Run `pytest -x`. The new tests must fail for the right reason.
6. **Green.** The smallest change that passes. Money stays `Decimal`; the service never commits;
   new queries avoid N+1 (check with a query counter if you load relationships in a loop).
7. **Refactor** with the tests green.
8. **Check everything:** `ruff check .`, `ruff format .`, `mypy`, `pytest`. Add the request to
   `loanlab.http` if you added an endpoint.
9. **Commit** in small steps: `test: ...` (red), `feat: ...` (green).

## Done when

- Every case links to a rule or a boundary, and each new test was seen failing once.
- Lint, format, types and all tests pass.
- Nothing in `instructor/` was read or changed.

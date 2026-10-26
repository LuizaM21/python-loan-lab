# Exam 2 — Key

## The bugs

See the table in `instructor/README.md`. For each bug, the expected test and fix:

| Bug | A test that catches it (lowest level) | Correct fix |
| --- | --- | --- |
| 01 | Unit: `open_loan("PERS", 50000.00, 12)` is accepted | `amount > product.max_amount` |
| 02 | Unit: `open_loan("PERS", 1000.00, 6)` is accepted | `months < product.min_months` |
| 03 | API: second POST with the same `Idempotency-Key` returns 200 | `201 if created else 200` |
| 04 | API: POST without `X-Api-Key` returns 401 and saves nothing | `if given is None or not compare_digest(...)` |
| 05 | Unit: same key, different amount -> `Conflict`, balance unchanged | restore `or existing.amount != amount` |
| 06 | Unit: repaying exactly the outstanding closes the loan | `amount > loan.outstanding` |
| 07 | Unit: `list_loans(status="closed")` total equals the number of closed loans | add the `where` to the count query too |
| 08 | Query count: `GET /api/loans?size=100` with 100+ loans runs a constant number of SELECTs | remove the per-row `refresh` |

Level points (2): bug 03 and 04 need an API test (unit tests cannot see status codes or headers).
Bug 08 at "query-count test" level gets full marks; a k6 test also gets full marks if it has a
threshold that fails with the bug (p95 with `DEMO_LOANS`), but note it is slower and noisier.

Do not give fix points if the fix changes a test's expected value instead of the code, or
"fixes" more than the rule (for example removing validation).

## Ticket notes

**Summary endpoint.** `totalRepaid` = sum of repayments; `percentRepaid` = repaid / amount × 100,
rounded half-up to 2 decimals; strings for money. 404 for unknown loans. Expect tests for a loan
with no repayments (0.00, 0.00%) and after partial and full repayment.

**Product filter.** Validate the code against the known products (400 `Unknown loan product.` or
similar); apply the filter to the count query as well (the bug 07 trap). Case-insensitive input is
a plus.

**Product stats.** One `GROUP BY` query (check with a query counter); products with no loans
either listed with zeros or omitted, as long as it is documented and tested.

---
name: triage-test-failure
description: Classifies a failing test or CI job (product bug, test bug, environment, or flaky), and for a product bug proves it with a minimal failing test and proposes the smallest fix. Use when pytest, CI, or a k6 threshold fails and the cause is not yet known.
---

# Triage a test failure

1. **Collect evidence:** the failure message and traceback, the test name and file, the command,
   the CI log or the API's JSON log lines (find the request by its `requestId`). For k6: the
   threshold that failed and the numbers.
2. **Re-run the single test 3 times** (`pytest -k <name> -x`).
   - Passes sometimes -> likely **flaky**: shared data between tests, exact list counts in the
     module-shared app, test order, real dates or time, timing.
3. **Check the environment:** right virtual environment and dependencies? An old API still
   running on port 5080? Was the API restarted after a code change? `MONGO_URL` set before lesson
   06 is done? For k6, was the API restarted before the run?
   Problem here -> **environment**.
4. **Check the test against the rule** in `CLAUDE.md` (Domain rules).
   The test's expected value breaks the rule -> **test bug**. Fix the test.
5. **The test matches the rule and the code does not -> product bug.**
   - Write the smallest failing test at the lowest level that shows it (unit before API).
   - Find the line (read the code, or `pytest --pdb`, or `breakpoint()`).
   - Propose the smallest fix that restores the rule. Don't change other behaviour.
   - Report:

```text
Title:     <what is wrong, in one line>
Area:      <layer and file / endpoint>
Severity:  <High / Medium / Low> because <impact on customers or money>
Expected:  <from the rule>
Actual:    <what happened, with values>
Evidence:  <test name, output>
Fix:       <file:line and the change>
```

6. Say which test level should have caught it, and whether that test was missing.

## Output

One line: `Classification: <product bug | test bug | environment | flaky>`, then the reasons,
then the report and fix (for product bugs) or the fix to the test or setup (for the others).

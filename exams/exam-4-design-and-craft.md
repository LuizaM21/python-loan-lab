# Exam 4 — Design and craft (lessons 11–19)

Time: 50 minutes. No notes, no internet, no AI.

Write your answers in `notes/exam-4-answers.md`. For part A, write the number and the letter.
Part C is oral, with your mentor (or record yourself and listen back).

Total for parts A and B: 40 points. Pass: 32.

## Part A — Multiple choice (1 point each)

**1.** `t = (1, [2]); t[1] += [3]` — what happens?
a) `t` becomes `(1, [2, 3])`, no error
b) `TypeError`, and `t` is still `(1, [2])`
c) `TypeError`, and `t` is `(1, [2, 3])` anyway
d) `SyntaxError`

**2.** `[f() for f in [lambda: i for i in range(3)]]` returns:
a) `[0, 1, 2]`
b) `[2, 2, 2]`
c) `[3, 3, 3]`
d) an error: `i` is not defined

**3.** A class defines `__eq__` but not `__hash__`. Its instances:
a) hash by `id()` as before
b) hash by their fields automatically
c) raise `TypeError` when the class is created
d) are unhashable: they can't go in a `set` or be `dict` keys

**4.** For `sum([Money("1"), Money("2")])` to work, `Money` needs:
a) `__radd__` that handles `0`
b) `__iadd__`
c) `__sum__`
d) nothing beyond `__add__`

**5.** Which is composition, not inheritance?
a) `class ValidationError(LoanLabError)`
b) `class Loan(Base)`
c) `RetryingCreditBureau(HttpCreditBureau(url))`
d) `class Outcome(IntEnum)`

**6.** `MaxActiveLoans` takes one counting function instead of a Session or a whole repository.
Which principle is that most directly?
a) Interface segregation
b) Liskov substitution
c) Open/closed
d) Single responsibility

**7.** The risk team's new rule is added as a new class, and `EligibilityPolicy` is not edited.
Which principle?
a) Liskov substitution
b) Single responsibility
c) Interface segregation
d) Open/closed

**8.** Which pattern **changes** an interface into the one your code expects?
a) Decorator
b) Adapter
c) Proxy
d) Facade

**9.** Strategy vs State:
a) In State, the object changes its own mode as things happen; in Strategy, the caller picks the algorithm
b) Strategy needs inheritance; State needs composition
c) They are two names for the same pattern
d) In State, the caller picks the state once at construction

**10.** The main risk of notifying observers in-process, before the transaction commits:
a) Observers can never unsubscribe
b) It always needs threads
c) A customer can be notified about a change that is then rolled back
d) It is always slower than a queue

**11.** Module `m` does `from urllib.request import urlopen` and calls `urlopen(...)`. To replace it
in a test, patch:
a) `"urllib.request.urlopen"`
b) `"m.urlopen"`
c) `"urllib.urlopen"`
d) `"builtins.urlopen"`

**12.** The main benefit of `create_autospec(CreditBureau, instance=True)` over `Mock()`:
a) It runs faster
b) It records calls (Mock doesn't)
c) It returns realistic values automatically
d) Calls to methods that don't exist, or with the wrong arguments, fail the test

**13.** Which bureau answer should be retried?
a) 503 Service Unavailable
b) 404 No credit history
c) 400 Bad Request
d) 200 with a body that is not valid JSON

**14.** A circuit breaker in the OPEN state:
a) calls the bureau with a shorter timeout
b) retries three times with backoff
c) fails fast without calling the bureau
d) returns the last good report

**15.** Loading 50 loans and all their repayments with `selectinload(Loan.repayments)` runs how many
SELECTs?
a) 1
b) 2
c) 50
d) 51

**16.** When does a new `Loan` get its `id`?
a) When it is created: `Loan(...)`
b) At `session.add(loan)`
c) At `session.close()`
d) At the flush that INSERTs it

**17.** With `expire_on_commit=True`: read a loan, commit, close the session, then read
`loan.customer_name`. What happens?
a) `DetachedInstanceError`
b) The old value is returned
c) `None`
d) The session reopens and reloads it

**18.** Under the lab's cleaning rules, `parse_amount("1,250")` returns:
a) `Decimal("1.25")`
b) a `CleaningError`: ambiguous
c) `Decimal("1250.00")`
d) `1250.0` (a float)

**19.** Where does "a PERS loan is at most 50,000.00 RON" belong?
a) In the CSV cleaner
b) In the service, the one place for business rules
c) In both the cleaner and the service, to be safe
d) Only in a database trigger

**20.** Which is a refactoring?
a) Rewriting the importer from scratch in a new module
b) Fixing IMP-102 and restructuring the loop in the same commit
c) Adding a dry-run feature
d) Extracting the parsing into a function, behaviour unchanged, tests green before and after

## Part B — Short answers (2 points each)

**21.** Explain "a variable is a name bound to an object". Then show the mutable default argument
bug and its fix in 4 lines of code.

**22.** Write a decorator `@log_calls(level=logging.INFO)` that logs the function name before each
call. It must keep the function's `__name__`.

**23.** Composition vs inheritance. When is inheritance the right choice? One example from this lab
for each.

**24.** Explain dependency inversion with `MinCreditScore` and `CreditBureau`. How does it make the
rule easy to test?

**25.** Adapter, Decorator, Facade: one sentence each on what it does, and one class from this lab
for each.

**26.** You test `RetryingCreditBureau`. Which double do you use for the inner bureau, and for
`sleep`? List four test cases with what each asserts.

**27.** The credit bureau becomes slow (5 s per call) at peak time. Name four measures in the code
or the setup that keep the rest of the API healthy, and say what each does.

**28.** What is the N+1 problem? Show it with loans and repayments, and give two fixes with their
SQLAlchemy names.

**29.** What is data cleaning? Give three principles you follow when you import branch files, each
with a reason.

**30.** Make the case for refactoring `loanlab/legacy/loan_import.py` in three sentences to a product
owner, and name your first two steps.

## Part C — Oral (mentor asks; not part of the 40 points)

Score each 1–4 like Exam 3. Aim for 3 or more on each.

1. Walk me through how Python looks up a name inside a nested function.
2. Live: write `parse_months(raw)` with its tests (5 minutes).
3. Draw the layers of the loan lab and say which way imports go.
4. Which design patterns have you used? Give two with the problem they solved.
5. Live: implement a tiny event bus with `subscribe` and `publish` where one failing handler can't
   break the others (8 minutes).
6. How do you test code that calls a third-party HTTP API? What do you mock, and what not?
7. Production incident: "the whole app is slow since 09:14". What do you do, minute by minute?
8. A colleague's endpoint runs 300 queries for 100 rows. How do you find it, prove it and fix it?
9. Live: here is a bug report and a 20-line function; write the failing test first (10 minutes; the
   mentor picks one of IMP-101 to IMP-106 against a fresh copy of the legacy file).
10. When would you refuse to refactor something, even if the code is bad?

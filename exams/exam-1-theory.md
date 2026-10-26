# Exam 1 — Theory

Time: 45 minutes. No notes, no internet, no AI.

Write your answers in `notes/exam-1-answers.md`. For part A, write the number and the letter
(for example `1 b`).

Total: 40 points. Pass: 32.

## Part A — Multiple choice (1 point each)

Choose one answer.

**1.** What does `Decimal(0.1) == Decimal("0.1")` return, and why?
a) `True`, both are exactly 0.1
b) `False`, `Decimal(0.1)` copies the binary error of the float
c) `True`, Decimal rounds both to 28 digits
d) It raises `TypeError`

**2.** What is wrong with `def add_tag(tag, tags=[]): tags.append(tag); return tags`?
a) Nothing
b) `append` returns `None`
c) The default list is created once and shared between calls
d) Lists cannot be default values

**3.** A pytest fixture has `scope="module"`. Its value is:
a) created once per test file and shared by its tests
b) created once per test
c) created once per test run
d) created once per class

**4.** Which is the best double for your own repository class in a unit test?
a) A mock that checks every method call
b) The production PostgreSQL database
c) No double; skip the test
d) A fake: a simple working version (in-memory)

**5.** In this lab, who commits the database transaction during an HTTP request?
a) Every service method
b) The repository
c) The request's `after_request` hook: commit on success, roll back on error
d) Nobody; SQLite autocommits

**6.** `session.flush()`:
a) sends pending SQL inside the open transaction, for example to get a new id
b) ends the transaction
c) clears the identity map
d) closes the connection

**7.** A list endpoint runs 1 query for 50 loans, then 1 more query per loan for its repayments. This is:
a) a deadlock
b) the N+1 problem
c) a lost update
d) a race condition

**8.** Two requests repay the same loan at the same moment on PostgreSQL. What stops both from reading the same balance?
a) `session.flush()`
b) An index on `outstanding`
c) `expire_on_commit=False`
d) `SELECT ... FOR UPDATE` (`with_for_update`)

**9.** A client retries `POST /repayments` after a timeout. The first request had succeeded. With an idempotency key, the server should:
a) return the original repayment, without charging again
b) charge again and return 201
c) return 500
d) return 404

**10.** Overpaying a loan by one cent (valid JSON, valid amount format) should return:
a) 200
b) 401
c) 409 Conflict
d) 500

**11.** Why does this API compare keys with `hmac.compare_digest`?
a) It is faster
b) It ignores case
c) It hashes the key
d) It takes the same time wherever the strings differ, so timing does not leak the key

**12.** In Django, to avoid N+1 when listing applications with their product (a ForeignKey):
a) `prefetch_related("product")` is the only option
b) `select_related("product")`
c) `annotate(Count("product"))`
d) `.only("id")`

**13.** `LoanProduct.objects.annotate(n=Count("applications"))` returns:
a) one number
b) a dict
c) each product with its own count `n`
d) only products with applications

**14.** For a MongoDB query `find({"loanReference": r}).sort("at", 1)`, the best index is:
a) `(loanReference, at)`
b) `(at, loanReference)`
c) `(at)` only
d) a text index

**15.** The GIL means that in CPython:
a) Python programs cannot use threads
b) only one thread runs Python bytecode at a time; threads still help when they wait on I/O
c) processes share one GIL
d) `asyncio` runs on many cores

**16.** You must call 500 slow REST APIs with a blocking HTTP library. Best simple choice:
a) a loop
b) a `ProcessPoolExecutor` with 500 processes
c) `time.sleep` between calls
d) a `ThreadPoolExecutor`

**17.** A Kubernetes readinessProbe fails. Kubernetes:
a) stops sending traffic to the pod until it passes again
b) restarts the container
c) deletes the Deployment
d) scales up

**18.** Why `COPY requirements.txt` + `pip install` before `COPY loanlab/` in a Dockerfile?
a) Python needs them first
b) Security
c) Layer caching: a code change does not reinstall dependencies
d) It makes the image run as non-root

**19.** `git bisect` helps you:
a) merge two branches
b) find the commit that introduced a bug with a binary search over history
c) split a commit
d) sign commits

**20.** A characterization test is:
a) a test of the UI
b) a performance test
c) a test written by the product owner
d) a test that pins the current output of code before you refactor it

## Part B — Short answers (2 points each)

Two or three sentences each.

**21.** Explain the application-factory pattern in Flask and one problem it solves for tests.

**22.** `flush()` vs `commit()`: why does `open_loan` call `flush()` before setting the reference?

**23.** What is a lost update? Give one pessimistic and one optimistic fix.

**24.** Explain how the idempotency key works in this API, including the case where the same key comes with a different amount.

**25.** Why is the hidden-bug approach (sample tests green, bug present) a realistic picture of real projects, and what do you do as a developer when you find one?

**26.** Flask + SQLAlchemy vs Django: two things each gives you, and which you'd choose for a new lending API and why.

**27.** What is the transactional outbox, and what problem in this app would it solve?

**28.** Threads, asyncio or processes for: (a) a Flask app under gunicorn, (b) computing schedules for 1 million loans?

**29.** Name four best practices in a production Python Dockerfile and why each matters.

**30.** You use an AI agent to write a feature. Name three things you do so you can trust and merge the result.

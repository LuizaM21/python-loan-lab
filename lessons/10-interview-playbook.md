# 10 — Interview playbook

Time: 30 minutes, plus practice.

Goal: tell your story, answer the likely questions, and show your work.

## Your story (60 seconds)

Write it in `notes/my-story.md`, then say it out loud 5 times.

1. Who you are: about 10 years in quality and performance engineering; Scala and Gatling at Mambu
   (core banking), Java and JMeter at Endava before that.
2. What you do best: you find what breaks under real load and real data, and now you fix it.
3. What you built recently: "A lending API in Python with Flask and SQLAlchemy, a Django version,
   a MongoDB event log, idempotent repayments, query-count tests, a performance fix from about
   6,000 queries to 2, Docker and Kubernetes, and a CI pipeline." Show the repo.
4. Why this role: you want to build the systems you've been testing, and you already know the
   Endava way of working with clients.

Be honest about experience: Python is newer for you than Scala. Show that you learn fast, test
everything, and think about production.

## STAR stories

Prepare 5. **S**ituation, **T**ask, **A**ction, **R**esult (with a number).

1. A performance problem you found and how it got fixed (Mambu migrations).
2. A disagreement with a developer or product owner, and how you solved it.
3. Something you automated or improved that saved the team time.
4. A time you learned something new fast (this lab).
5. A time requirements were unclear and you moved forward anyway ("high autonomy, limited
   information" is in the job ad).

## Likely questions, and where you learned the answer

| Question | Lesson |
| --- | --- |
| Why `Decimal`? Mutable default arguments? Decorators? Generators? | 01 |
| How do you test a service? Fakes vs mocks? TDD? | 02 |
| Design a REST endpoint for repayments. Status codes. Idempotency. | 03 |
| Flask app factory, `g`, error handling, WSGI vs ASGI | 03 |
| Sessions, transactions, N+1, locking, migrations | 04 |
| Flask vs Django; `select_related` vs `prefetch_related` | 05 |
| When MongoDB? Index design. Outbox pattern. | 06 |
| The GIL; threads vs asyncio vs processes; find a bottleneck | 07 |
| Dockerfile best practices; probes; requests and limits | 08 |
| Git workflow, CI/CD, code review, AI agents | 09 |
| Live coding | katas |
| Dunder methods, closures, generators, `Protocol` vs `ABC` | 11 |
| Composition vs inheritance; SOLID with examples; how do you structure a service? | 12 |
| Which design patterns have you used? Adapter vs Decorator vs Facade | 13 |
| Strategy vs State; Observer and the outbox; Chain of Responsibility | 14 |
| Mocking: what and where; retries, timeouts, circuit breakers; an incident | 15 |
| What does the ORM do? N+1, eager loading, locking, ORM vs SQL | 16 |
| What is data cleaning? ETL; exporting large data | 17 |
| How do you fix a bug? Walk me through one. | 18 |
| When and how do you refactor? Convince your PO. | 19 |

### Small system design (have one ready)

"Design a loan repayment service": API (idempotency key), database (balances in PostgreSQL, row
lock or optimistic version), events (outbox -> queue -> consumers like notifications), read side
(paging, indexes, a cache with TTL for product data), operations (structured logs with request
id, metrics p95/p99, health probes, horizontal scaling behind a load balancer), testing (unit,
API, contract, load). Draw it in 5 boxes.

### Topics outside this lab

**C++ (nice to have).** Be honest: you studied it (master's in embedded systems) and haven't used
it recently. Know how it meets Python: C extensions, `pybind11`, `ctypes`/`cffi`, and why NumPy
is fast (loops in C, not in Python).

**FastAPI.** Async, type-hint based validation with Pydantic, OpenAPI docs generated. If asked:
"I'd port the Flask API in a day; the service layer would not change."

**Celery / queues.** Background jobs with a broker (Redis, RabbitMQ). Idempotent tasks, retries
with backoff.

If you don't know something: say so, then say how you would find out.

## Questions to ask them

1. What does a typical project look like: team size, client, stack, how long?
2. How do you test and release? How long does the pipeline take?
3. Flask, Django or FastAPI on the project? Which databases?
4. How do developers and testers work together on your teams?
5. How do teams use AI coding tools today?
6. What would success look like in my first 6 months?

## The day before

- Run all tests, katas and the API once. Push. Check the pipeline is green.
- Say your story and two STAR stories out loud.
- Re-read your notes from lessons 04 and 07 (transactions and the performance fix).
- Sleep.

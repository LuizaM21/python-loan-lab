# Study plan: 5 days to interview-ready

Target role: **Senior Developer (Python)**, backend: Python, Flask/Django, ORMs, unit tests and
debugging, Git, autonomy with limited information. Nice to have: Linux, Docker, Kubernetes,
MongoDB, C++.

You have 5 days, about 4–5 hours each. Do the lessons in order. Each lesson has:

- **Learn**: the ideas, in short form.
- **In this repo**: where you can see the idea in the code.
- **Do**: exercises. Build real features, test-first. Run them.
- **Check yourself**: questions. Answer them out loud, without notes.
- **Say it in the interview**: sentences you can reuse.

Keep your own notes in the `notes/` folder. Interviewers like it when you show real work.

## Before you start

1. Follow the main [README](../README.md) until the API runs and all sample tests pass.
2. Push the repo to your own GitHub account. Work on branches, merge with pull requests.
   Then you can show the history in the interview.
3. Do **not** open `instructor/`. It has the reference solutions, exam answers and the hidden bugs.

## Day 1 — Python and tests

| Time | Lesson |
| --- | --- |
| 75 min | [01 Python for a JVM developer](01-python-for-jvm-developers.md) |
| 90 min | [02 Tests and TDD as a developer](02-tests-and-tdd.md) |
| 45 min | Katas: `two_sum`, `brackets`, `top_k` (see [katas](#katas)) |

## Day 2 — APIs and databases

| Time | Lesson |
| --- | --- |
| 90 min | [03 REST APIs with Flask](03-rest-apis-with-flask.md) |
| 90 min | [04 Databases: SQLAlchemy, transactions, migrations](04-databases-sqlalchemy.md) |
| 30 min | Practice bug hunt 1 (end of lesson 04) |

## Day 3 — Django and MongoDB

| Time | Lesson |
| --- | --- |
| 90 min | [05 Django for a Flask developer](05-django.md) |
| 60 min | [06 MongoDB and the event log](06-mongodb.md) |
| 45 min | Katas: `binary_search`, `intervals`, `lru_cache` |

## Day 4 — Performance and shipping

| Time | Lesson |
| --- | --- |
| 90 min | [07 Performance and concurrency](07-performance-and-concurrency.md) |
| 75 min | [08 Docker, Kubernetes and Linux](08-docker-kubernetes-linux.md) |
| 30 min | Practice bug hunt 2 (end of lesson 08) |
| 30 min | Katas: `rate_limiter`, `coin_change` |

## Day 5 — Senior topics and exams

| Time | Lesson |
| --- | --- |
| 60 min | [09 Git, CI/CD, code review and AI agents](09-git-ci-review-ai.md) |
| 30 min | [10 Interview playbook](10-interview-playbook.md) |
| 45 min | [Exam 1 — theory](../exams/exam-1-theory.md) |
| 90 min | [Exam 2 — practical: fix and build](../exams/exam-2-practical.md) |
| 45 min | [Exam 3 — mock interview](../exams/exam-3-mock-interview.md) |

Day 5 is long. If needed, do Exam 3 on the evening before the interview.

You are ready when you pass all three exams. See [exams/README.md](../exams/README.md).

## Days 6–8 — Design and craft

A second module, for interviews that go deeper into design: Python internals, composition and
SOLID, design patterns, mocks and production, the ORM, data cleaning, bug fixing and refactoring.
Every lesson builds on the loan domain and adds real code: a credit bureau client, eligibility rules,
an event bus, a CSV importer and a legacy importer with six production bugs.

### Day 6 — Python and design

| Time | Lesson |
| --- | --- |
| 90 min | [11 Python fundamentals, the deep version](11-python-fundamentals.md) |
| 90 min | [12 Composition, structure in code, and SOLID](12-composition-and-solid.md) |
| 75 min | [13 Design patterns: creational and structural](13-design-patterns.md) |

### Day 7 — Behaviour, production and data access

| Time | Lesson |
| --- | --- |
| 90 min | [14 Behavioral patterns](14-behavioral-patterns.md) |
| 120 min | [15 Mocks, and handling things in production](15-mocks-and-production.md) |
| 90 min | [16 The ORM in depth](16-orm-in-depth.md) |

### Day 8 — Data, bugs and refactoring

| Time | Lesson |
| --- | --- |
| 120 min | [17 Data cleaning, loading, and extracting data back out](17-data-cleaning-and-extraction.md) |
| 120 min | [18 Bug fixing: from a ticket to a regression test](18-bug-fixing.md) |
| 150 min | [19 A case for refactoring: why, then how](19-refactoring-case.md) |
| 50 min | [Exam 4 — design and craft](../exams/exam-4-design-and-craft.md) |

Do 17, 18, 19 in that order: the cleaner from 17 is reused in 18's fixes, and 18's tests are the
safety net for 19's refactoring. Day 8 is long; split it over two days if you need to.

### Exercises

Like the katas, the design exercises have tests that are switched off by default:

```bash
pytest -m exercise                                     # all of them
pytest -m exercise tests/exercises/test_clean.py       # one
```

| Exercise | Lesson | Practises |
| --- | --- | --- |
| `exercises/money_value.py` | 11 | the data model: dunder methods, immutability, hashing |
| `exercises/eligibility_rules.py` | 12 | open/closed, composition, a Protocol |
| `exercises/schedule_strategies.py` | 14 | Strategy + registry |
| `exercises/circuit_breaker.py` | 14, 15 | State; resilience; mocks with a fake clock |
| `exercises/loan_repository.py` | 16 | Repository; eager loading; query counts; GROUP BY |
| `loanlab/importer/clean.py` | 17 | data cleaning, test-first |

## Katas

Interview-style algorithm exercises in `katas/`, with tests in `tests/katas/`. The tests are
switched off by default so CI stays green. Run them on purpose:

```bash
pytest -m kata                              # all katas
pytest -m kata tests/katas/test_two_sum.py  # one kata
```

Time-box each one to 20 minutes, talking out loud as if in a live-coding interview: the plan, the
complexity, the edge cases, then the code. Commit each kata when it is green.

## How the hidden bugs work

Your mentor can turn on small bugs in the app. The sample tests stay green. Only a good new test
finds a bug. As a developer you do two things: **prove** the bug with a failing test, then **fix**
it. The test stays as a regression test.

You can also practise alone:

```bash
instructor/bug.sh random 1   # turns on one random bug; it does not say which
```

Run your tests. If all stay green, your tests missed the bug. Add tests until one fails, then fix
the code so it passes. Check:

```bash
instructor/bug.sh list       # shows which bug was on
instructor/bug.sh reset      # turns every bug off (it notices when you already fixed it)
```

Restart the API after you turn a bug on or off. On Windows, run the script in Git Bash.

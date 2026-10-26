# 07 — Performance and concurrency

Time: 90 minutes.

Goal: measure, find and fix a real bottleneck in Python, and choose the right concurrency model.

This is your home ground. In the interview, this is where you stop being "learning Python" and
become "the developer who can prove it's fast".

## Learn: the method

1. **Measure** under a realistic load. Report p50, p95, p99 and the error rate, not the average.
2. **Profile** to find where the time goes. Never guess.
3. **Pin behaviour** with a characterization test before you change anything.
4. **Fix** the biggest cost first.
5. **Measure again** with the same load. Report before/after.

## Learn: Python tools

| Tool | Use |
| --- | --- |
| `python -m cProfile -s cumtime script.py` | deterministic profiler: calls and time per function |
| `py-spy top --pid <pid>` / `py-spy record -o flame.svg --pid <pid>` | sampling profiler on a running server, no code change |
| `timeit` | micro-benchmarks |
| SQLAlchemy event listener / `echo=True` | count and see SQL statements |
| k6 | load: `http_req_duration` p95, `http_req_failed` |
| `tracemalloc` | where memory is allocated |

## Learn: the GIL and concurrency

Only one thread runs **Python bytecode** at a time (the Global Interpreter Lock). Threads still
help when they **wait** (network, database, disk): the GIL is released while waiting.

| Workload | Use | Why |
| --- | --- | --- |
| Many blocking calls (DB, HTTP with `requests`) | threads (`ThreadPoolExecutor`, gunicorn `--threads`) | GIL released during I/O |
| Many concurrent I/O calls with async libraries | `asyncio` (`httpx.AsyncClient`, FastAPI) | thousands of waits on one thread |
| CPU-heavy (big calculations, parsing) | processes (`ProcessPoolExecutor`, gunicorn workers) | each process has its own GIL |
| A web app like this one | gunicorn: workers = processes, `--threads` per worker | both |

Rule of thumb for gunicorn: workers ≈ CPU cores (×2 + 1 is the classic default), threads for
I/O-heavy apps. Never call a blocking function inside `async def` without `run_in_executor`.

Python 3.13 has an experimental free-threaded build without the GIL. Know it exists.

## Learn: the usual suspects in a Python backend

1. **N+1 queries** and pulling whole tables into Python to count or sum them.
2. Missing **indexes** (check with `EXPLAIN`).
3. Work done **per request** that could be cached (with a TTL and a clear invalidation rule).
4. Long transactions and lock waits.
5. Too few workers, or blocking calls in an async app.
6. Big JSON responses without paging.

## In this repo

| File | Shows |
| --- | --- |
| `loanlab/stats.py` | `portfolio_stats`: correct, slow: `1 + 2 × N` queries |
| `loanlab/seed.py` | `seed_demo`: N random loans, the same every run |
| `perf/smoke.js` | a k6 smoke test |
| `perf/stats-load.js` | load on `GET /api/stats/portfolio` |

## Do

### 1. Measure before

```bash
DEMO_LOANS=3000 flask --app loanlab.api run --port 5080     # startup takes a few seconds
k6 run perf/stats-load.js
```

Write down p50, p95, p99 and requests per second in `notes/day-4.md`.

### 2. Profile

```python
# notes/profile_stats.py
import cProfile, pstats
from loanlab.api import create_app
from loanlab.stats import portfolio_stats

app = create_app({"DATABASE_URL": "sqlite://", "DEMO_LOANS": 2000, "LOG_LEVEL": "WARNING"})
with app.extensions["loanlab.sessionmaker"]() as session:
    cProfile.runctx("portfolio_stats(session)", globals(), locals(), "stats.prof")
pstats.Stats("stats.prof").sort_stats("cumulative").print_stats(15)
```

Also count the SELECTs with your query counter from lesson 04. How many for 2,000 loans?

### 3. Pin the behaviour

Write `test_output_on_known_data`: seed 200 demo loans and assert the **whole** stats dictionary,
with values captured from the current (slow) code. This is a characterization test: the
refactor must not change a single digit.

### 4. Fix it

Rewrite `portfolio_stats` so the database does the work: one `GROUP BY` query for the active
loans per product, one `SUM` for the repayments. Same output. Add a test: the number of SELECTs
does not grow with the number of loans (≤ 3 for 300 loans).

### 5. Measure after

Restart the API, run `k6 run perf/stats-load.js` again, and write the before/after table in your
notes. This table is an interview story.

### 6. Concurrency on purpose

- Run the API under gunicorn: `gunicorn "loanlab.api:create_app()" --preload -w 4 --threads 4 -b 0.0.0.0:5080`
  (Linux/macOS/WSL; on Windows use Docker, lesson 08). Run the load again. What changed?
  Why `--preload`? Read the comment at the end of the start-up code in `loanlab/api/__init__.py`.
- Write a k6 script with 20 virtual users repaying 300.00 on the **same** 1,000.00 loan at once,
  each with its own idempotency key, against gunicorn with several workers. Expect: 3 × 201, the
  rest are 500 `database is locked` (look at the JSON log). The money is still right (outstanding
  100.00): the losers rolled back. Why does SQLite do this? (Hint: a deferred transaction reads,
  then needs to upgrade to a write lock while another writer holds it.) On PostgreSQL in lesson 08,
  `FOR UPDATE` makes them wait instead, and you get 3 × 201 and the rest 409.
- Then improve the API: a lock or serialization failure is not a bug in the request, so it should
  not be a 500. Map SQLAlchemy's `OperationalError` for "database is locked" to **503** with a
  `Retry-After: 1` header, test-first. (The idempotency key makes a client retry safe.)
- Small experiment in `notes/`: `ThreadPoolExecutor` with 10 threads running `time.sleep(0.1)` 10
  times vs computing `sum(range(10**7))` 10 times. Time both. Explain with the GIL.

## Check yourself

1. What is the GIL? When do threads help in Python and when not?
2. Threads, asyncio or processes: (a) call 500 REST APIs, (b) resize 10,000 images, (c) a Flask app?
3. What happens if you call `requests.get()` inside an `async def` endpoint?
4. Why report p95/p99 and not the average?
5. Walk me through how you found and fixed the slow stats endpoint.
6. When is a cache the right fix, and what is the hard part?
7. Why is 503 + `Retry-After` better than 500 for a lock conflict, and what makes the retry safe?
8. How many gunicorn workers and threads would you start with on a 2-CPU pod?

## Say it in the interview

- "I measure first, with p95 and p99 under a realistic load, then profile, then pin the output
  with a characterization test, then fix the biggest cost, then measure again."
- "On the stats endpoint I went from about 6,000 queries to 2 by moving the aggregation into SQL.
  p95 dropped from X ms to Y ms." (Use your numbers.)
- "I've done load testing for years with Gatling and k6; now I also fix what I find."

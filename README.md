# Loan lab

A small lending API for learning **Python backend development**: Flask, SQLAlchemy, Django,
MongoDB, tests and TDD, performance and concurrency, Docker and Kubernetes, CI, and AI-assisted
development.

Customers take **loans** from three loan products. The API quotes a repayment schedule, opens
loans, and records repayments safely: an API key for writes, idempotency keys so a retried
payment is never charged twice, and row locks for concurrent repayments.

The products, rates and limits are **fictional**. This is not financial advice.

- API: Python 3.12, Flask + SQLAlchemy 2.0, in `loanlab/`. Data is in SQLite by default and is
  reset on every start: two sample loans come back. PostgreSQL and MongoDB via Docker Compose.
- Django version of the domain, for comparison: `django_lab/`.

**Start here after setup: [lessons/README.md](lessons/README.md)**, the 5-day study plan, plus
3 more days on design and craft (lessons 11–19: Python internals, SOLID, design patterns, mocks and
production, the ORM, data cleaning, bug fixing and refactoring).

## Install the tools

| Tool | Check | Download |
| --- | --- | --- |
| Git | `git --version` | https://git-scm.com |
| Python 3.12 or newer | `python --version` | https://www.python.org/downloads/ |
| Docker Desktop (lessons 06, 08) | `docker --version` | https://www.docker.com/products/docker-desktop/ |
| k6 (lesson 07) | `k6 version` | https://grafana.com/docs/k6/latest/set-up/install-k6/ |
| kind (lesson 08, optional) | `kind version` | https://kind.sigs.k8s.io/docs/user/quick-start/ |

On Windows, use Git Bash for the `instructor/bug.sh` script. All other commands work in PowerShell too.

## Start the app

### 1. Clone and install

```bash
git clone https://github.com/<your-account>/python-loan-lab.git
cd python-loan-lab
python -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

### 2. Start the API

```bash
flask --app loanlab.api run --port 5080
```

Wait for `Running on http://127.0.0.1:5080`.

- Ready-made requests for PyCharm or VS Code (REST Client): `loanlab.http`
- Every request prints one JSON log line with its request id and duration.

In PyCharm: open the folder, set the interpreter to `.venv`, and create a "Flask server" run
configuration with target `loanlab.api` and additional options `--port 5080`.

### 3. Try it once

1. `GET http://localhost:5080/api/loans`: you see Maria Ionescu (`LN-0001`) and Andrei Stan (`LN-0002`).
2. Quote: `POST /api/loans/quote` with `{"productCode": "PERS", "amount": 10000, "months": 12}`.
   The monthly payment is `878.69`; month 12 is `878.74`.
3. Open it: `POST /api/loans` with header `X-Api-Key: lab-dev-key` and
   `{"customerName": "Ana Pop", "productCode": "PERS", "amount": 10000, "months": 12}`.
   You get 201, reference `LN-0003`, and a `Location` header.
4. Repay 500 with headers `X-Api-Key: lab-dev-key` and `Idempotency-Key: try-it-1`: 201.
   Send the same request again: 200, and the balance only went down once.

## Run the tests

| Level | Command | Folder | Sample tests |
| --- | --- | --- | --- |
| Unit + API | `pytest` | repo root | 5 samples. Add yours. |
| Katas (interview algorithms) | `pytest -m kata` | repo root | 10 katas, red until you solve them |
| Design exercises (lessons 11–19) | `pytest -m exercise` | repo root | 6 exercises, red until you solve them |
| Django lab | `python manage.py test lending` | `django_lab` | 1 |
| Lint, format, types | `ruff check .`, `ruff format --check .`, `mypy` | repo root | |
| Performance smoke | `k6 run perf/smoke.js` (API must be running) | repo root | 1 |

GitHub Actions runs lint, tests, the k6 smoke and a Docker build on every push:
`.github/workflows/ci.yml`.

## Repo map

| Path | What |
| --- | --- |
| `loanlab/schedule.py`, `money.py`, `products.py` | Pure domain: loan maths, money rounding, the products |
| `loanlab/services.py` | Rules: validation, opening loans, repayments with idempotency and locking |
| `loanlab/models.py`, `db.py` | SQLAlchemy models and engine setup |
| `loanlab/api/` | Flask app factory, routes, request parsing, API key check, error handling |
| `loanlab/events.py` | Event log: in memory, and MongoDB (you finish it in lesson 06) |
| `loanlab/stats.py` | Portfolio statistics: correct but slow (you fix it in lesson 07) |
| `loanlab/credit.py` | Credit bureau client: adapter, timeouts, retries (lessons 13–15) |
| `loanlab/eligibility.py` | Eligibility rules composed into a policy (lessons 12, 14) |
| `loanlab/notifications.py` | Event bus and observers (lesson 14) |
| `loanlab/importer/` | CSV extract, cleaning (you write it in lesson 17), report export |
| `loanlab/legacy/loan_import.py` | The old importer: six production bugs (lesson 18), then refactored (lesson 19) |
| `exercises/`, `tests/exercises/` | Design exercises for lessons 11–19 |
| `data/` | Two messy branch CSV files (synthetic) |
| `tests/` | Sample unit and API tests and shared fixtures. Add yours here. |
| `katas/`, `tests/katas/` | Interview algorithm exercises |
| `django_lab/` | The same domain in Django (lesson 05) |
| `perf/` | k6 scripts |
| `Dockerfile`, `docker-compose.yml`, `k8s/` | Containers: API + PostgreSQL + MongoDB; Kubernetes manifests |
| `lessons/` | 19 lessons and the study plan |
| `exams/` | 4 exams |
| `CLAUDE.md`, `.claude/` | Context, skills and a reviewer agent for AI coding agents |
| `ci/` | GitLab CI version of the pipeline, for study |
| `notes/` | Your notes |
| `instructor/` | For the mentor only: hidden bugs, solutions and answer keys. Do not open. |

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///loanlab.sqlite3` | Any SQLAlchemy URL, e.g. `postgresql+psycopg://user:pw@host/db` |
| `API_KEY` | `lab-dev-key` | Key for write endpoints (`X-Api-Key` header) |
| `RESET_DATABASE` | `1` | Drop and recreate the tables on start |
| `SEED` | `1` | Add the two sample loans to an empty database |
| `DEMO_LOANS` | `0` | Add this many random loans on start (lesson 07) |
| `MONGO_URL` | empty | Use MongoDB for the event log (lesson 06) |
| `LOG_LEVEL` | `INFO` | Log level |

## If something fails

| What you see | What to do |
| --- | --- |
| `flask: command not found` / `No module named flask` | Activate the virtual environment: `source .venv/bin/activate`, then `pip install -r requirements-dev.txt`. |
| `Address already in use` | An old API still runs. Stop it (Ctrl+C), or close the old terminal or PyCharm run. |
| The API shows old behaviour | Restart it. Flask does not reload without `--debug`. |
| `401` on a POST | Add the header `X-Api-Key: lab-dev-key`. |
| `400 Idempotency-Key header is required` | Repayments need an `Idempotency-Key` header with any unique text. |
| `database is locked` under load | SQLite allows one writer at a time. Use PostgreSQL via `docker compose up` (lesson 08). |
| `NotImplementedError` from `MongoEventLog` | `MONGO_URL` is set, but lesson 06 isn't done yet. Unset it. |
| k6 thresholds fail on a second run | Restart the API. Data from the last run is still there. |
| `bug.sh` fails with `does not apply` | Commit or stash your changes, then `instructor/bug.sh reset`. |

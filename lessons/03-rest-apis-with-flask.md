# 03 — REST APIs with Flask

Time: 90 minutes.

Goal: understand how this Flask API is built, design endpoints well, and add one.

## Learn: Flask in this repo

```python
def create_app(config=None, *, today=date.today, events=None) -> Flask:   # application factory
    app = Flask(__name__)
    ...                                       # engine, sessions, event log, seed
    app.register_blueprint(api)               # the routes, grouped in a Blueprint
    @app.after_request                        # commit or roll back the request's transaction
    @app.errorhandler(LoanLabError)           # domain errors -> status + JSON body
    return app

@api.post("/loans")
@require_api_key                              # a decorator guards the write
def open_loan():
    body = json_body()                        # parse + validate the SHAPE
    loan = service().open_loan(...)           # the service validates the RULES
    response = jsonify(loan_json(loan))
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_loan", loan_id=loan.id)
    return response
```

| Idea | Why |
| --- | --- |
| **Application factory** | Each test builds its own app with its own config (in-memory DB, fixed clock). No global state. |
| **Blueprint** | Groups routes; registered on the app. |
| **Thin views** | Views read the request and write the response. Rules live in `LoanService`. |
| **`g`** | Per-request storage. The DB session lives in `g.db`. |
| **`current_app`** | The app handling this request (for config and shared objects). |
| **Unit of work per request** | One session, one transaction: commit on success, roll back on any error status. |
| **Error handlers** | Every error is JSON: `{"code": "...", "message": "..."}`, even 404 for an unknown URL. |

Flask is **WSGI** and synchronous: one request per worker thread. In production it runs under
**gunicorn** (processes × threads). FastAPI is **ASGI** (async), with validation and OpenAPI built in.

## Learn: API design that interviewers ask about

| Status | When | In this repo |
| --- | --- | --- |
| 200 OK | read, or a safe retry | `GET`, repeated repayment with the same key |
| 201 Created + `Location` | a new resource | `POST /api/loans`, first repayment |
| 400 Bad Request | invalid input | bad amount, unknown product |
| 401 Unauthorized | missing or wrong credentials | no `X-Api-Key` |
| 403 Forbidden | authenticated, not allowed | (not here) |
| 404 Not Found | no such resource | unknown loan id |
| 409 Conflict | valid request, but the state forbids it | overpaying, closed loan, key reuse |
| 422 | well-formed but semantically invalid (some teams use it instead of 400) | |
| 500 | a bug. Never on purpose. | |

**Idempotency.** `GET`, `PUT` and `DELETE` are idempotent by definition; `POST` is not. A client
that times out and retries a payment must not pay twice. Fix: the client sends an
`Idempotency-Key`; the server stores it with the result (here: unique column on `repayments`) and
returns the original result for a retry (200), or 409 if the same key comes with a different body.

**Money in JSON** travels as a string (`"878.69"`). This API also parses JSON numbers with
`parse_float=Decimal`, so `50000.01` never becomes a float.

**Security basics.** Keys in headers, never in URLs (URLs end up in logs). Compare secrets with
`hmac.compare_digest` (constant time). Validate every input. Return the same error for "wrong key"
and "no key".

## In this repo

| File | Shows |
| --- | --- |
| `loanlab/api/__init__.py` | factory, request id, JSON logs, unit of work, error handlers |
| `loanlab/api/routes.py` | every endpoint |
| `loanlab/api/payloads.py` | reading bodies (types) and writing JSON (camelCase, money as strings) |
| `loanlab/api/auth.py` | the API key decorator |
| `loanlab.http` | ready-made requests for PyCharm or VS Code |

## Do

Start the API (`flask --app loanlab.api run --port 5080`) and try every request in `loanlab.http`.
Watch the JSON log line for each request in the terminal.

API tests go in `tests/api/test_loans_api.py` and use the `client` fixture.

### 1. Created means Created

`POST /api/loans` returns 201, a `Location` header, and `GET` on that location returns the same
body. Use a unique customer name (`f"Ana {uuid.uuid4().hex[:8]}"`): the app is shared.

### 2. Security

No key, a wrong key, `LAB-DEV-KEY` (case), and an empty key: all 401, and nothing saved.

### 3. Input shape

`amount` missing, `true`, `"abc"`; `months` as `"12"` or `12.5`; a body that is a JSON list, or
not JSON at all: all 400 with a message. Also: `"amount": 50000.01` as a JSON **number** must be
rejected for PERS (why is this a good test of `parse_float=Decimal`?).

### 4. Repayment contract

First call 201, a retry with the same key 200 and the same body, outstanding reduced once. No
`Idempotency-Key` -> 400. Overpaying -> 409 and nothing changed.

### 5. Feature: list a loan's repayments

The support team asks: "Show all repayments of a loan." Build it test-first:

`GET /api/loans/<id>/repayments` -> 200 and a list, oldest first:
`[{"id": 1, "loanId": 3, "amount": "100.00", "paidOn": "2026-03-01"}, ...]`.
Unknown loan -> 404 `"Loan not found."`. A rejected repayment never appears. No API key needed
to read.

Add the request to `loanlab.http`. Commit: `feat: list repayments of a loan`.

### 6. Debug a request

Put `breakpoint()` in `repay()` in `routes.py`, run one API test with `pytest -k repay -s`, step
with `n`, inspect with `p body`, continue with `c`. Then do the same with the PyCharm debugger.
Remove the breakpoint.

## Check yourself

1. Why an application factory instead of a global `app = Flask(...)`?
2. Where do the business rules live, and why not in the views?
3. 400 vs 409 vs 422: which for "overpaying a loan", and why?
4. How does the idempotency key stop a double charge? What happens on a retry with a different amount?
5. Why send money as a JSON string? What does `parse_float=Decimal` protect against?
6. Why compare API keys with `hmac.compare_digest`?
7. WSGI vs ASGI. Where do gunicorn and uvicorn fit?

## Say it in the interview

- "I keep views thin: parse and validate the shape, call a service that owns the rules, map
  domain errors to status codes in one place."
- "Any endpoint that moves money gets an idempotency key, because clients retry on timeouts."
- "Every error has the same JSON shape with a request id, so support can trace it in the logs."

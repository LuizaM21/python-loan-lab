# 06 — MongoDB and the event log

Time: 60 minutes.

Goal: model data in MongoDB, use indexes and the aggregation pipeline from Python, and plug a
second implementation behind an interface.

## Learn: MongoDB in one page

| SQL | MongoDB |
| --- | --- |
| database / table / row | database / collection / document (BSON, like JSON) |
| schema in DDL | flexible; the schema lives in your code (validate it there, or with `$jsonSchema`) |
| `WHERE a = 1 AND at >= x` | `find({"a": 1, "at": {"$gte": x}})` |
| `SELECT type, at` | projection `{"_id": 0, "type": 1, "at": 1}` |
| `ORDER BY at LIMIT 10` | `.sort("at", 1).limit(10)` |
| `GROUP BY type, COUNT(*)` | `aggregate([{"$group": {"_id": "$type", "count": {"$sum": 1}}}])` |
| `INSERT ... ON CONFLICT UPDATE` | `update_one(filter, {"$set": ...}, upsert=True)` |
| JOIN | embed related data in the document, or `$lookup` (use sparingly) |
| transaction | single-document writes are atomic; multi-document needs a replica set + session |

**Indexes**: compound index field order is **equality, sort, range** (ESR). A query on
`loanReference` sorted by `at` wants the index `(loanReference, at)`.

**Money**: integer cents or `Decimal128`. Never floats.

**When Mongo**: append-only events, flexible or nested documents, very high write volume, data
read whole by key. **When SQL**: money balances, constraints across rows, joins, reporting,
transactions over several entities. A loan's balance stays in PostgreSQL; its event history is a
good fit for Mongo.

## Learn: the event log in this app

`loanlab/events.py` defines a `Protocol`:

```python
class EventLog(Protocol):
    def record(self, event_type: str, loan_reference: str, data: dict) -> None: ...
    def history(self, loan_reference: str) -> list[dict]: ...
    def counts_by_type(self) -> dict[str, int]: ...
```

The service records `loan_opened`, `repayment_recorded` and `loan_closed`. The app uses
`InMemoryEventLog` unless `MONGO_URL` is set; then it uses `MongoEventLog`, which is your job.

Notice a real design problem: the event is recorded **outside** the database transaction. If the
commit fails after `record()`, the log says something happened that didn't. The production
answer is the **transactional outbox**: write the event to an `outbox` table in the same
transaction, and publish it from there.

## In this repo

| File | Shows |
| --- | --- |
| `loanlab/events.py` | the protocol, the in-memory version, the `MongoEventLog` stubs |
| `loanlab/services.py` | where events are recorded |
| `GET /api/loans/<id>/events` | the history through the API |

## Do

```bash
pip install -r requirements-dev.txt      # includes mongomock: an in-memory fake MongoDB
docker run -d --name mongo -p 27017:27017 mongo:7     # optional, for the real thing
```

### 1. A contract test first

Write `tests/unit/test_event_log.py` with **one** set of tests that runs against **every**
implementation, using a parametrized fixture:

```python
@pytest.fixture(params=["memory", "mongo"])
def log(request):
    if request.param == "memory":
        return InMemoryEventLog()
    mongomock = pytest.importorskip("mongomock")
    log = MongoEventLog(mongomock.MongoClient()["loanlab"]["events"])
    log.ensure_indexes()
    return log
```

Rules to test: history is per loan, oldest first, without `_id`; the caller's `data` dict is not
changed; `counts_by_type` counts per type; an unknown loan has an empty history. Run: the memory
tests pass, the Mongo ones fail. That's your to-do list.

### 2. Implement `MongoEventLog`

`ensure_indexes` (compound index for `history`), `record` (`insert_one` with a **new** dict: it
adds `_id` to what you pass), `history` (`find` + projection + `sort`), `counts_by_type`
(`aggregate` with `$group`). Add `from pymongo import ASCENDING` at the top.

### 3. Run against a real MongoDB

```bash
MONGO_URL=mongodb://localhost:27017 flask --app loanlab.api run --port 5080
```

Open and repay a loan through `loanlab.http`, then `GET /api/loans/<id>/events`. In
`mongosh`: `use loanlab`, `db.events.find().sort({at: -1}).limit(5)`, and
`db.events.find({loanReference: "LN-0003"}).sort({at: 1}).explain("executionStats")`: find
`IXSCAN`. Drop the index and look again: `COLLSCAN`.

### 4. Design note

In `notes/day-3.md`: sketch the transactional outbox for this app (table, columns, who reads it,
what happens on a crash between insert and publish). Five to ten lines.

## Check yourself

1. Embedding vs referencing: how do you decide?
2. What order do you put fields in a compound index, and why?
3. Which writes are atomic in MongoDB without a transaction?
4. Why test two implementations with one contract test?
5. What problem does the transactional outbox solve?
6. When would you pick MongoDB over PostgreSQL for a feature, and when definitely not?

## Say it in the interview

- "I'd keep balances in a relational database and put the append-only event history in MongoDB,
  behind an interface, with one contract test suite for both implementations."
- "I design Mongo indexes from the queries: equality fields, then sort, then range, and I check
  with `explain()`."

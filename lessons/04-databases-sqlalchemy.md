# 04 — Databases: SQLAlchemy, transactions, migrations

Time: 90 minutes.

Goal: use the SQLAlchemy 2.0 ORM well: sessions, transactions, queries without N+1, locking, and
schema changes with Alembic.

## Learn: the ORM in this repo

```python
class Loan(Base):
    __tablename__ = "loans"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str | None] = mapped_column(String(20), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))  # NUMERIC, never FLOAT, for money
    status: Mapped[str] = mapped_column(String(10), default="active", index=True)
    repayments: Mapped[list[Repayment]] = relationship(back_populates="loan", order_by="Repayment.id")


# 2.0-style queries: build a statement, then execute it
loans = session.scalars(select(Loan).where(Loan.status == "active").order_by(Loan.id).limit(20)).all()
total = session.scalar(select(func.count()).select_from(Loan))
```

| Idea | Meaning |
| --- | --- |
| **Session** | A unit of work. Tracks the objects you loaded or added; writes them on `flush`. |
| **Identity map** | One Python object per row per session. `session.get(Loan, 1)` twice -> the same object. |
| `flush()` vs `commit()` | `flush` sends SQL inside the open transaction (e.g. to get `loan.id`). `commit` ends it. |
| Who commits? | Never the service. One request = one transaction, committed in `after_request`. |
| `expire_on_commit` | Off here, so objects stay readable after commit. On by default. |
| Lazy loading | `loan.repayments` runs a query the first time you touch it. |
| **N+1** | 1 query for the list + 1 per row for a relationship. Fix: `selectinload(Loan.repayments)` (2 queries) or `joinedload` (1 JOIN). |
| `with_for_update` | `SELECT ... FOR UPDATE`: lock the row until commit. Stops two repayments both reading the same balance. SQLite ignores it; PostgreSQL honours it. |
| SAVEPOINT | `with session.begin_nested():` roll back part of a transaction and keep going. |

## Learn: transactions and isolation

- **ACID**: atomic, consistent, isolated, durable.
- Isolation levels: read committed (PostgreSQL default), repeatable read, serializable.
- **Lost update**: two transactions read outstanding = 1000, both subtract 600, both commit.
  Pessimistic fix: `FOR UPDATE`. Optimistic fix: a `version` column checked in the `UPDATE`
  (`version_id_col` in SQLAlchemy); on conflict, retry.
- Keep transactions **short**. Never call a slow HTTP service while holding a row lock.

## Learn: migrations with Alembic

`create_all()` only creates missing tables. It never changes an existing one. Real projects
version the schema:

```bash
alembic init migrations                 # once; then set target_metadata = Base.metadata in env.py
alembic revision --autogenerate -m "add customer_name index"
alembic upgrade head                    # apply
alembic downgrade -1                    # undo the last one
```

Autogenerate is a **draft**: always read it. Safe changes on a live table: add a nullable column,
backfill in batches, then make it NOT NULL in a later release.

## In this repo

| File | Shows |
| --- | --- |
| `loanlab/models.py` | typed models, indexes, unique constraints, a one-to-many relationship |
| `loanlab/db.py` | engine setup; SQLite in memory with `StaticPool`; the SQLite SAVEPOINT recipe |
| `loanlab/services.py` | `flush` to get an id, `with_for_update`, filtered count, paging |
| `loanlab/stats.py` | a deliberately slow, N+1 implementation (fixed in lesson 07) |

See the SQL: `create_engine(url, echo=True)` in `db.py` prints every statement. Turn it on once.

## Do

### 1. Watch the SQL

Turn on `echo=True`, run `pytest tests/unit/test_loan_service.py -s`, and read the statements:
`BEGIN`, the `INSERT`, the `UPDATE` that sets the reference, `ROLLBACK`. Turn it off again.

### 2. A query counter

Write a context manager in `tests/support.py` that counts `SELECT` statements with
`sqlalchemy.event.listen(engine, "before_cursor_execute", ...)`. Use it to assert that
`GET /api/loans?size=100` with 100+ loans runs a **constant** number of queries.
(Create loans with `loanlab.seed.seed_demo`.) Keep this helper: you need it again in lesson 07.

### 3. Paging and filters

Service tests: page 2 of size 2 returns the 3rd and 4th loans in id order; `status="closed"`
returns only closed loans and `total` counts only those; an unknown status is a `ValidationError`.

### 4. Feature: search loans by customer

The support team asks: "Find loans by part of the customer's name."

`GET /api/loans?customer=pop` -> case-insensitive "contains" match, combined with `status` and
paging; `total` counts matches only. `%` and `_` in the search are plain text, not wildcards
(`"50%"` matches the name `"Dan 50% Off"` only). A blank search returns everything. Add an index
on `customer_name`.

Test-first, at the service level, then one API test. Hint: `Loan.customer_name.ilike(..., escape="\\")`.

### 5. Alembic

```bash
pip install alembic
alembic init migrations
```

In `migrations/env.py`: `from loanlab.models import Base` and `target_metadata = Base.metadata`;
in `alembic.ini`: `sqlalchemy.url = sqlite:///alembic-demo.sqlite3`. Then generate the initial
migration, apply it, add a nullable `purpose` column (`String(50)`) to `Loan`, generate a second
migration and **read it**. Write in `notes/day-2.md` what you would change before running it on
a production table with 10 million rows.

### 6. Think about concurrency

In `notes/day-2.md`: two requests repay 600.00 on a 1,000.00 loan at the same moment, on
PostgreSQL. Walk through what happens with and without `with_for_update`.

### Practice bug hunt 1

`instructor/bug.sh random 1`. Run your tests. If one fails, read it, find the line, fix the code,
keep the test. If all stay green, add tests (boundaries, status codes, side effects) until one
fails. Then `instructor/bug.sh list` and `instructor/bug.sh reset`.

## Check yourself

1. What is the identity map? What does `session.get()` do when the object is already loaded?
2. `flush` vs `commit`. Why does `open_loan` flush twice?
3. Explain N+1 and two ways to fix it in SQLAlchemy.
4. What is a lost update? Pessimistic vs optimistic locking.
5. Why must the service not commit?
6. Why does `create_all` not replace migrations?
7. How do you add a NOT NULL column to a large live table safely?

## Say it in the interview

- "I treat the session as a unit of work: one transaction per request, committed at the edge,
  never inside the service."
- "I catch N+1 in tests with a query counter, not in production dashboards."
- "For money movements I lock the row with `SELECT ... FOR UPDATE` or use optimistic versioning,
  and I keep the transaction short."

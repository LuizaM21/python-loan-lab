# 16 — The ORM in depth

Time: 90 minutes.

Goal: explain what an ORM does for you and what it costs, control exactly which SQL runs, and hide
storage behind a repository.

Lesson 04 covered the basics (models, sessions, transactions, Alembic). This lesson is about how
the Session **thinks**, and how to keep the query count under control.

## Learn: what an ORM is

An Object-Relational Mapper maps **classes to tables, objects to rows, attributes to columns,
references to foreign keys**. SQLAlchemy has two layers:

- **Core**: SQL expressions in Python (`select(Loan.reference, func.sum(...))`), returning rows.
- **ORM**: mapped classes, the Session, relationships, change tracking, returning objects.

The Session implements three enterprise patterns:

| Pattern | What it does | What you see |
| --- | --- | --- |
| **Identity map** | One object per row per session | `session.get(Loan, 1) is session.scalars(select(Loan).where(Loan.id == 1)).one()` is `True` |
| **Unit of work** | Tracks new, changed and deleted objects; writes them all at `flush` | You change `loan.outstanding`; no SQL runs until a flush |
| **Lazy loading** (a proxy) | Related objects load when first touched | `loan.repayments` runs a `SELECT` the first time |

## Learn: object states

```python
loan = Loan(...)        # transient: not in a session, no id
session.add(loan)       # pending: in the session, not yet in the database
session.flush()         # persistent: INSERT sent, loan.id is set (inside the open transaction)
session.commit()        # still persistent; transaction ended
session.close()         # detached: no session; lazy loads now fail
```

Check with `sqlalchemy.inspect(loan).pending`, `.persistent` and so on.

| Setting / call | Effect |
| --- | --- |
| `flush()` | Sends pending SQL **inside** the transaction. Nothing is permanent yet. |
| autoflush | Before a query, the session flushes, so the query sees your own changes |
| `commit()` | Flush + end the transaction |
| `expire_on_commit=True` (default) | After commit, every attribute is reloaded on next access. After `close()`, that raises `DetachedInstanceError`. |
| `expire_on_commit=False` (this repo, `db.py`) | Objects keep their values after commit, so the API can build JSON after the request's commit |
| `refresh(obj)` / `expire(obj)` | Reload now / reload on next access |
| `begin_nested()` | A SAVEPOINT: roll back part of a transaction (lesson 19's importer, one per row) |
| After a failed flush | The session must be `rollback()`ed before any further use: `PendingRollbackError` (lesson 18, IMP-106) |

## Learn: control the SQL

**N+1**: one query for the list, then one more per row for a relationship. 100 loans with
repayments = 101 queries. Lesson 07's `stats.py` did this with thousands of rows.

| Loading strategy | SQL | Use for |
| --- | --- | --- |
| `lazy="select"` (default) | One `SELECT` per object, on first access | Single objects, rarely-used relations |
| `selectinload(Loan.repayments)` | 1 extra query: `... WHERE loan_id IN (1, 2, ...)` | Collections (one-to-many). Usually the best default. |
| `joinedload(Repayment.loan)` | `LEFT OUTER JOIN` in the same query | Many-to-one (each repayment's loan). For collections it multiplies rows. |
| `raiseload("*")` | Raises instead of loading | In tests: prove that nothing lazy-loads |
| Select columns, not entities | `select(Loan.reference, Loan.outstanding)` | Reports and exports: no objects, no tracking, much faster (`importer/export.py`) |
| Aggregate in SQL | `func.sum`, `group_by` | Never load 10,000 rows to add them up in Python |

Writes:

```python
# read-modify-write: needs a row lock (repay() uses with_for_update) or a version check
loan.outstanding -= amount

# atomic update in ONE statement: the database does the arithmetic, no lost update possible
session.execute(
    update(Loan).where(Loan.id == loan_id, Loan.outstanding >= amount)
    .values(outstanding=Loan.outstanding - amount)
)  # check result.rowcount == 1, else: not enough outstanding

# bulk insert of many rows: one statement, not one per object
session.execute(insert(Loan), [{"customer_name": ..., ...}, ...])
```

**Optimistic locking**: add a `version` column and `__mapper_args__ = {"version_id_col": version}`.
SQLAlchemy adds `WHERE version = :old` to every UPDATE and raises `StaleDataError` if someone else
changed the row first. Good when conflicts are rare; **pessimistic** `SELECT ... FOR UPDATE`
(`repay()`) when they are common or the cost of a retry is high.

## Learn: SQLAlchemy vs Django ORM

| Task | SQLAlchemy 2.0 | Django |
| --- | --- | --- |
| Query | `session.scalars(select(Loan).where(Loan.status == "active"))` | `Loan.objects.filter(status="active")` (lazy QuerySet) |
| Many-to-one eager | `joinedload` | `select_related("product")` |
| One-to-many eager | `selectinload` | `prefetch_related("repayments")` |
| Group by | `select(Loan.product_code, func.sum(Loan.outstanding)).group_by(...)` | `.values("product_code").annotate(total=Sum("outstanding"))` |
| Atomic update | `update(Loan).values(outstanding=Loan.outstanding - x)` | `.update(outstanding=F("outstanding") - x)` |
| Row lock | `with_for_update=True` | `select_for_update()` inside `transaction.atomic()` |
| Transaction | The caller's `session.commit()` | `transaction.atomic()`; autocommit otherwise |
| Pattern | Data Mapper (models don't save themselves) | Active Record (`loan.save()`) |

## Learn: when not to use the ORM

The ORM is great for use cases that load a few objects, change them and save. It is the wrong tool
for: big reports (select columns, or plain SQL), bulk loads (`insert` with many rows, or PostgreSQL
`COPY`), complex analytics (window functions, CTEs: Core or SQL views). Always look at the SQL it
produces (`echo=True`, or a query counter) before you trust it with volume.

## Learn: the Repository pattern

A repository gives **domain-language methods** over storage: `count_active_for(name)`, not
`select(func.count())...`. The service and the rules depend on it (or on one of its methods, like
`MaxActiveLoans` does), not on the Session. Benefits: queries in one place, easy fakes in tests,
storage can change. Cost: one more layer; for simple CRUD the Session is already a repository plus
a unit of work, so don't wrap it just to wrap it.

## In this repo

| File | Shows |
| --- | --- |
| `loanlab/models.py` | typed mappings, relationship with `cascade="all, delete-orphan"`, indexes |
| `loanlab/db.py` | `expire_on_commit=False`, SQLite SAVEPOINT recipe, `StaticPool` for in-memory |
| `loanlab/services.py` | flush to get an id, `with_for_update` row lock, the service never commits |
| `loanlab/stats.py` | N+1 (until you fixed it in lesson 07) |
| `loanlab/importer/export.py` | column select, SQL `SUM` + outer join, `yield_per` streaming |

## Do

### 1. Watch the object states

In `notes/orm_states.py`, create a `Loan`, then print `inspect(loan)` states and `loan.id` after
each of: creating it, `add`, `flush`, `commit`, closing the session. Then show the identity map
(`get` twice, `is`). Then make a session with `expire_on_commit=True`, read a loan, commit, close,
and read an attribute: which exception, and why does this repo set `expire_on_commit=False`?

### 2. Exercise: a repository

`exercises/loan_repository.py` describes `LoanRepository`. Make
`pytest -m exercise tests/exercises/test_loan_repository.py` green. The tests **count queries**:
`with_repayments()` must run exactly 2 SELECTs for 20 loans, `outstanding_by_product()` exactly 1
with a `GROUP BY`. Then plug `repo.count_active_for` into `MaxActiveLoans` and `repo.count_all_for`
into your `FirstLoanCap` from lesson 12 in a test.

### 3. Prove there is no lazy loading

Write a test that loads loans with `options(selectinload(Loan.repayments), raiseload("*"))` and reads
every repayment. Then remove `selectinload` and see the error. This is how you guard an endpoint
against N+1 in CI.

### 4. Atomic update

Write (in a branch, not in `services.py`) a `repay_atomic` that uses one
`update(...).where(..., Loan.outstanding >= amount)` and `rowcount`. Compare with the current
`with_for_update` version: which needs fewer round trips? Which keeps the idempotency check and the
event recording simpler?

### 5. Stretch: the same in Django

In `django_lab`, write the "total amount per product of submitted applications" query with
`values(...).annotate(Sum(...))`. Print `str(queryset.query)` and compare the SQL with SQLAlchemy's.

## Check yourself

1. What is an ORM? Name the three patterns the Session implements.
2. The four object states. When does a loan get its `id`?
3. `flush` vs `commit`. What is autoflush?
4. What does `expire_on_commit` do, and why is it `False` here?
5. What is N+1? Three ways to avoid it. `selectinload` vs `joinedload`: which for a collection?
6. Read-modify-write vs atomic update. Optimistic vs pessimistic locking.
7. When would you not use the ORM?
8. Data Mapper vs Active Record. Which is SQLAlchemy, which is Django?
9. What does a repository add on top of the Session? When is it not worth it?

## Say it in the interview

- "The Session is a unit of work with an identity map. I flush when I need a generated id, and the
  request, not the service, decides to commit."
- "I watch query counts in tests. Collections get `selectinload`, many-to-one gets `joinedload`, and
  reports select columns and aggregate in SQL. That took a stats endpoint from thousands of queries
  to two."
- "For balances I either lock the row or do an atomic `UPDATE ... SET outstanding = outstanding - x
  WHERE outstanding >= x`, never a plain read-modify-write."

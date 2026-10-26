# 05 — Django for a Flask developer

Time: 90 minutes.

Goal: build with Django's ORM, views, migrations and admin, and compare it with Flask + SQLAlchemy.

The job asks for "Flask/Django". You built with Flask; now do the same domain in Django, in
`django_lab/`: customers submit loan **applications** for the same three products.

## Learn: Django in one page

```text
django_lab/
  manage.py               the command line: runserver, makemigrations, migrate, test, shell
  config/settings.py      INSTALLED_APPS, DATABASES, MIDDLEWARE, TIME_ZONE...
  config/urls.py          the root URL table
  lending/                an "app": models, views, urls, admin, migrations, tests
```

| Flask + SQLAlchemy | Django |
| --- | --- |
| micro-framework, choose your parts | batteries included: ORM, migrations, admin, auth, forms |
| `Session` + `select()` (data mapper) | `Model.objects.filter(...)` (active record: `obj.save()`) |
| explicit transaction per request | autocommit; `transaction.atomic()` for a block |
| Alembic | `makemigrations` / `migrate`, built in |
| Blueprint routes | `urls.py` + views |
| REST: hand-written, flask-smorest | Django REST Framework (DRF) |
| pytest + test client | `django.test.TestCase` (each test in a rolled-back transaction) + `self.client` |

## Learn: the QuerySet API

```python
Application.objects.filter(status="approved", product__code="PERS")  # __ follows relations
Application.objects.exclude(amount__lt=1000).order_by("-created_at")[:20]
Application.objects.select_related("product")  # FK: one JOIN. Fixes N+1.
LoanProduct.objects.prefetch_related("applications")  # reverse FK: one extra query
LoanProduct.objects.annotate(n=Count("applications"))  # a value PER ROW
Application.objects.aggregate(total=Sum("amount"))  # ONE value for the whole set
Sum("applications__amount", filter=Q(applications__status="approved"))  # conditional aggregate
Application.objects.filter(pk=1).update(status="approved")  # one UPDATE, no load
F("amount") * 2  # refer to a column in the database
```

QuerySets are **lazy**: no SQL runs until you iterate, slice with a step, call `len()`,
`list()`, or `bool()`.

## In this repo

| File | Shows |
| --- | --- |
| `django_lab/lending/models.py` | `LoanProduct`, `Application`, `TextChoices`, a `CheckConstraint` |
| `django_lab/lending/migrations/0002_seed_products.py` | a **data** migration with `RunPython` |
| `django_lab/lending/views.py` | `products` done; `applications` and `product_stats` are yours |
| `django_lab/lending/tests.py` | one sample `TestCase` |

Run it (from `django_lab/`):

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8000         # http://localhost:8000/api/products/  and /admin/
python manage.py test lending
python manage.py sqlmigrate lending 0001
python manage.py shell
```

## Do

Write the tests first, in `lending/tests.py`. Use `self.client.post(url, data=body,
content_type="application/json")`.

### 1. Read the migrations

`python manage.py sqlmigrate lending 0001` and read the SQL for the check constraint. Why is the
product list a **data migration** and not a fixture loaded by hand?

### 2. Create an application

`POST /api/applications/` with `{"customerName", "productCode", "amount", "months"}` -> 201 and
the application (status `submitted`). Same rules and messages as the Flask app: unknown product,
amount and term limits per product, at most 2 decimals, name required and at most 100
characters. Invalid -> 400 `{"message": ...}` and nothing saved. (Hint: the view needs
`@csrf_exempt` because it is a JSON API, not a browser form.)

### 3. List applications without N+1

`GET /api/applications/?status=approved`. Unknown status -> 400. Prove it uses **one** query with
`self.assertNumQueries(1)`, however many rows there are. (Each row shows its `productCode`, so
without `select_related` you get N+1.)

### 4. Product stats in one query

`GET /api/products/stats/` -> per product: number of applications and the total amount of
**approved** ones (`"0.00"` when none), in one query: `annotate` + conditional `Sum`.

### 5. A useful admin

`list_display`, `list_filter` (status, product), `search_fields` (customer name),
`list_select_related`, and an admin action "Approve selected applications" that changes only
`submitted` ones, with one `UPDATE`. Try it at `/admin/`.

### 6. Compare

In `notes/day-3.md`, half a page: the same feature (create + list) in Flask + SQLAlchemy and in
Django. What did each framework give you for free? What would you choose for a new loan
service, and why?

## Check yourself

1. `select_related` vs `prefetch_related`: which for a FK, which for a reverse FK or M2M?
2. `annotate` vs `aggregate`?
3. When does a QuerySet hit the database?
4. Why does `Model.objects.filter(pk=1).update(x=F("x") - 10)` avoid a race that `obj.x -= 10; obj.save()` has?
5. How does `TestCase` keep tests isolated?
6. Two branches both add migration `0003`. What happens and how do you fix it?
7. Describe a request's path: middleware -> URL resolver -> view -> response -> middleware.

## Say it in the interview

- "I've built the same domain in Flask with SQLAlchemy and in Django. Django gives me admin,
  auth and migrations out of the box; Flask gives me explicit control of the transaction and the
  layers. I'm comfortable in both."
- "I check query counts in tests: `assertNumQueries` in Django, an engine event listener in
  SQLAlchemy."

"""Data migration: the three fictional products, same as the Flask app."""

from decimal import Decimal

from django.db import migrations

PRODUCTS = [
    ("PERS", "Flexi Personal", "0.0990", "1000.00", "50000.00", 6, 60),
    ("AUTO", "Auto Plus", "0.0750", "5000.00", "150000.00", 12, 84),
    ("HOME", "Home Start", "0.0550", "20000.00", "500000.00", 60, 360),
]


def add_products(apps, schema_editor):
    LoanProduct = apps.get_model("lending", "LoanProduct")  # the historical model, not an import
    for code, name, rate, low, high, min_m, max_m in PRODUCTS:
        LoanProduct.objects.create(
            code=code,
            name=name,
            annual_rate=Decimal(rate),
            min_amount=Decimal(low),
            max_amount=Decimal(high),
            min_months=min_m,
            max_months=max_m,
        )


def remove_products(apps, schema_editor):
    apps.get_model("lending", "LoanProduct").objects.filter(code__in=[p[0] for p in PRODUCTS]).delete()


class Migration(migrations.Migration):
    dependencies = [("lending", "0001_initial")]

    operations = [migrations.RunPython(add_products, remove_products)]

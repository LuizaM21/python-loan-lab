"""Django version of the lending domain, for lesson 05.

Same products as the Flask app (fictional). Here customers submit loan APPLICATIONS.
"""

from django.db import models
from django.db.models import Q


class LoanProduct(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    annual_rate = models.DecimalField(max_digits=6, decimal_places=4)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    min_months = models.PositiveIntegerField()
    max_months = models.PositiveIntegerField()

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name}"


class Application(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    customer_name = models.CharField(max_length=100)
    product = models.ForeignKey(LoanProduct, on_delete=models.PROTECT, related_name="applications")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    months = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SUBMITTED, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="application_amount_positive")]

    def __str__(self) -> str:
        return f"#{self.id} {self.customer_name} {self.product.code} {self.amount}"

"""Lesson 05 reference solution for the admin exercise."""

from django.contrib import admin

from .models import Application, LoanProduct


@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "annual_rate", "min_amount", "max_amount", "min_months", "max_months"]
    search_fields = ["code", "name"]


@admin.action(description="Approve selected applications")
def approve(modeladmin, request, queryset):
    updated = queryset.filter(status=Application.Status.SUBMITTED).update(status=Application.Status.APPROVED)
    modeladmin.message_user(request, f"{updated} application(s) approved.")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["id", "customer_name", "product", "amount", "months", "status", "created_at"]
    list_filter = ["status", "product"]
    search_fields = ["customer_name"]
    list_select_related = ["product"]
    actions = [approve]

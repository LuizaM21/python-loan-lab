from django.contrib import admin

from .models import Application, LoanProduct

# Lesson 05, exercise 5: make these admin screens useful (list_display, list_filter, search_fields,
# list_select_related, and an "approve selected" action).
admin.site.register(LoanProduct)
admin.site.register(Application)

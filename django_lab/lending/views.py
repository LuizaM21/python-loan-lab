"""JSON views for lesson 05. `products` is done; the rest are your exercises."""

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from .models import LoanProduct


def product_json(product: LoanProduct) -> dict:
    return {
        "code": product.code,
        "name": product.name,
        "annualRate": f"{product.annual_rate:.4f}",
        "minAmount": f"{product.min_amount:.2f}",
        "maxAmount": f"{product.max_amount:.2f}",
        "minMonths": product.min_months,
        "maxMonths": product.max_months,
    }


@require_GET
def products(request: HttpRequest) -> JsonResponse:
    return JsonResponse([product_json(p) for p in LoanProduct.objects.all()], safe=False)


@require_http_methods(["GET", "POST"])
def applications(request: HttpRequest) -> JsonResponse:
    """Lesson 05, exercises 2 and 3:
    POST: create an application (validate against the product limits) -> 201
    GET:  list applications, optional ?status=, without N+1 queries
    """
    return JsonResponse({"message": "Not implemented yet: lesson 05."}, status=501)


@require_GET
def product_stats(request: HttpRequest) -> JsonResponse:
    """Lesson 05, exercise 4: per product, the number of applications and the total amount
    of APPROVED ones, in ONE query (annotate)."""
    return JsonResponse({"message": "Not implemented yet: lesson 05."}, status=501)

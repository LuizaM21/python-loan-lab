"""Lesson 05 reference solution. Copy over django_lab/lending/views.py to try it."""

import json
from decimal import Decimal, InvalidOperation

from django.db.models import Count, Q, Sum
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .models import Application, LoanProduct


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


def application_json(application: Application) -> dict:
    return {
        "id": application.id,
        "customerName": application.customer_name,
        "productCode": application.product.code,
        "amount": f"{application.amount:.2f}",
        "months": application.months,
        "status": application.status,
        "createdAt": application.created_at.isoformat(),
    }


def bad_request(message: str) -> JsonResponse:
    return JsonResponse({"message": message}, status=400)


@require_GET
def products(request: HttpRequest) -> JsonResponse:
    return JsonResponse([product_json(p) for p in LoanProduct.objects.all()], safe=False)


@csrf_exempt  # an API called with JSON, not a browser form (in DRF you'd use token auth instead)
@require_http_methods(["GET", "POST"])
def applications(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        return list_applications(request)
    return create_application(request)


def list_applications(request: HttpRequest) -> JsonResponse:
    status = request.GET.get("status")
    queryset = Application.objects.select_related("product")  # one JOIN instead of one query per row
    if status is not None:
        if status not in Application.Status.values:
            return bad_request("Status must be submitted, approved or rejected.")
        queryset = queryset.filter(status=status)
    return JsonResponse([application_json(a) for a in queryset], safe=False)


def create_application(request: HttpRequest) -> JsonResponse:
    try:
        body = json.loads(request.body or b"null", parse_float=Decimal)
    except ValueError:
        body = None
    if not isinstance(body, dict):
        return bad_request("Request body must be a JSON object.")

    name = body.get("customerName")
    if not isinstance(name, str) or not name.strip():
        return bad_request("Customer name is required.")
    if len(name.strip()) > 100:
        return bad_request("Customer name must be 100 characters or fewer.")

    product = LoanProduct.objects.filter(code=str(body.get("productCode", "")).upper()).first()
    if product is None:
        return bad_request("Unknown loan product.")

    raw_amount, months = body.get("amount"), body.get("months")
    if isinstance(raw_amount, bool) or not isinstance(raw_amount, (int, Decimal, str)):
        return bad_request("Amount must be a number.")
    try:
        amount = Decimal(raw_amount)
    except InvalidOperation:
        return bad_request("Amount must be a number.")
    if not amount.is_finite() or amount != amount.quantize(Decimal("0.01")):
        return bad_request("Amount must have at most 2 decimals.")
    if not product.min_amount <= amount <= product.max_amount:
        return bad_request(
            f"Amount must be between {product.min_amount} and {product.max_amount} RON for {product.name}."
        )
    if isinstance(months, bool) or not isinstance(months, int):
        return bad_request("Months must be a whole number.")
    if not product.min_months <= months <= product.max_months:
        return bad_request(
            f"Term must be between {product.min_months} and {product.max_months} months for {product.name}."
        )

    application = Application.objects.create(customer_name=name.strip(), product=product, amount=amount, months=months)
    response = JsonResponse(application_json(application), status=201)
    response["Location"] = f"/api/applications/{application.id}/"
    return response


@require_GET
def product_stats(request: HttpRequest) -> JsonResponse:
    rows = LoanProduct.objects.annotate(
        application_count=Count("applications"),
        approved_amount=Sum("applications__amount", filter=Q(applications__status=Application.Status.APPROVED)),
    )
    return JsonResponse(
        [
            {
                "productCode": row.code,
                "applications": row.application_count,
                "approvedAmount": f"{row.approved_amount or Decimal('0'):.2f}",
            }
            for row in rows
        ],
        safe=False,
    )

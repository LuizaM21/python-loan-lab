"""Lesson 05 reference tests. Copy over django_lab/lending/tests.py, then: python manage.py test lending"""

from decimal import Decimal

from django.test import TestCase

from .models import Application, LoanProduct


def post(client, body):
    return client.post("/api/applications/", data=body, content_type="application/json")


class ProductsApiTests(TestCase):
    def test_lists_the_three_products(self):
        # execute

        response = self.client.get("/api/products/")

        # verify

        self.assertEqual(response.status_code, 200)
        self.assertEqual([p["code"] for p in response.json()], ["AUTO", "HOME", "PERS"])


class CreateApplicationTests(TestCase):
    def test_creates_an_application(self):
        # execute

        response = post(
            self.client, {"customerName": " Ana Pop ", "productCode": "PERS", "amount": "10000.00", "months": 12}
        )

        # verify

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["customerName"], "Ana Pop")
        self.assertEqual(body["status"], "submitted")
        self.assertEqual(Application.objects.count(), 1)

    def test_accepts_the_product_limits(self):
        for amount, months in [("1000.00", 6), ("50000.00", 60)]:
            with self.subTest(amount=amount, months=months):
                response = post(
                    self.client, {"customerName": "Edge", "productCode": "PERS", "amount": amount, "months": months}
                )
                self.assertEqual(response.status_code, 201)

    def test_rejects_invalid_input_and_saves_nothing(self):
        cases = [
            ({"productCode": "PERS", "amount": "1000", "months": 12}, "Customer name is required."),
            ({"customerName": "A", "productCode": "GOLD", "amount": "1000", "months": 12}, "Unknown loan product."),
            (
                {"customerName": "A", "productCode": "PERS", "amount": "999.99", "months": 12},
                "Amount must be between 1000.00 and 50000.00 RON for Flexi Personal.",
            ),
            (
                {"customerName": "A", "productCode": "PERS", "amount": "50000.01", "months": 12},
                "Amount must be between 1000.00 and 50000.00 RON for Flexi Personal.",
            ),
            (
                {"customerName": "A", "productCode": "PERS", "amount": "1000", "months": 5},
                "Term must be between 6 and 60 months for Flexi Personal.",
            ),
            (
                {"customerName": "A", "productCode": "PERS", "amount": "1000.001", "months": 12},
                "Amount must have at most 2 decimals.",
            ),
            (
                {"customerName": "A", "productCode": "PERS", "amount": "1000", "months": "12"},
                "Months must be a whole number.",
            ),
        ]
        for body, message in cases:
            with self.subTest(body=body):
                response = post(self.client, body)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["message"], message)
        self.assertEqual(Application.objects.count(), 0)


class ListApplicationsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        pers, auto = LoanProduct.objects.get(code="PERS"), LoanProduct.objects.get(code="AUTO")
        for i in range(5):
            Application.objects.create(customer_name=f"C{i}", product=pers, amount=Decimal("2000"), months=12)
        Application.objects.create(
            customer_name="Approved",
            product=auto,
            amount=Decimal("9000"),
            months=24,
            status=Application.Status.APPROVED,
        )

    def test_filters_by_status(self):
        response = self.client.get("/api/applications/?status=approved")
        self.assertEqual([a["customerName"] for a in response.json()], ["Approved"])

    def test_rejects_an_unknown_status(self):
        self.assertEqual(self.client.get("/api/applications/?status=weird").status_code, 400)

    def test_uses_one_query_whatever_the_number_of_rows(self):
        with self.assertNumQueries(1):
            response = self.client.get("/api/applications/")
        self.assertEqual(len(response.json()), 6)

    def test_product_stats(self):
        with self.assertNumQueries(1):
            response = self.client.get("/api/products/stats/")
        stats = {row["productCode"]: row for row in response.json()}
        self.assertEqual(stats["PERS"], {"productCode": "PERS", "applications": 5, "approvedAmount": "0.00"})
        self.assertEqual(stats["AUTO"], {"productCode": "AUTO", "applications": 1, "approvedAmount": "9000.00"})
        self.assertEqual(stats["HOME"]["applications"], 0)

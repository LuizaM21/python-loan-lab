"""Run from the django_lab folder: python manage.py test lending"""

from django.test import TestCase


class ProductsApiTests(TestCase):
    def test_lists_the_three_products(self):
        # execute

        response = self.client.get("/api/products/")

        # verify

        self.assertEqual(response.status_code, 200)
        codes = [p["code"] for p in response.json()]
        self.assertEqual(codes, ["AUTO", "HOME", "PERS"])

    # Add your own tests below this line.

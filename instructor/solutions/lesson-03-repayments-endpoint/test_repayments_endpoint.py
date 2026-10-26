"""Lesson 03 reference tests for GET /api/loans/<id>/repayments. Copy into tests/api."""

import uuid

KEY = {"X-Api-Key": "lab-dev-key"}


def new_loan(client):
    body = {"customerName": f"Ana {uuid.uuid4().hex[:6]}", "productCode": "PERS", "amount": "1000.00", "months": 12}
    return client.post("/api/loans", json=body, headers=KEY).get_json()


def repay(client, loan_id, amount):
    headers = {**KEY, "Idempotency-Key": uuid.uuid4().hex}
    return client.post(f"/api/loans/{loan_id}/repayments", json={"amount": amount}, headers=headers)


class TestListRepayments:
    def test_lists_repayments_oldest_first(self, client):
        # setup

        loan = new_loan(client)
        repay(client, loan["id"], "100.00")
        repay(client, loan["id"], "50.50")

        # execute

        response = client.get(f"/api/loans/{loan['id']}/repayments")

        # verify

        assert response.status_code == 200
        body = response.get_json()
        assert [r["amount"] for r in body] == ["100.00", "50.50"]
        assert all(r["loanId"] == loan["id"] and r["paidOn"] == "2026-03-01" for r in body)

    def test_a_new_loan_has_an_empty_list(self, client):
        loan = new_loan(client)
        assert client.get(f"/api/loans/{loan['id']}/repayments").get_json() == []

    def test_a_rejected_repayment_is_not_listed(self, client):
        loan = new_loan(client)
        assert repay(client, loan["id"], "5000.00").status_code == 409
        assert client.get(f"/api/loans/{loan['id']}/repayments").get_json() == []

    def test_unknown_loan_is_404(self, client):
        response = client.get("/api/loans/999999/repayments")
        assert response.status_code == 404
        assert response.get_json()["message"] == "Loan not found."

    def test_reading_needs_no_api_key(self, client):
        loan = new_loan(client)
        assert client.get(f"/api/loans/{loan['id']}/repayments").status_code == 200

"""Reference API tests: status codes, headers, auth, error contract, and that rejected writes save nothing."""

import uuid

import pytest
from flask.testing import FlaskClient

KEY = {"X-Api-Key": "lab-dev-key"}


def unique(name: str) -> str:
    return f"{name} {uuid.uuid4().hex[:8]}"


def open_loan(client: FlaskClient, headers=KEY, **overrides):
    body = {"customerName": unique("Ana Pop"), "productCode": "PERS", "amount": "10000.00", "months": 12, **overrides}
    return client.post("/api/loans", json=body, headers=headers)


def all_names(client: FlaskClient) -> set[str]:
    names, page = set(), 1
    while True:
        body = client.get(f"/api/loans?size=100&page={page}").get_json()
        names |= {loan["customerName"] for loan in body["items"]}
        if page * 100 >= body["total"]:
            return names
        page += 1


class TestReadEndpoints:
    def test_health(self, client):
        assert client.get("/api/health").get_json() == {"status": "ok", "database": "ok"}

    def test_lists_the_three_products(self, client):
        products = client.get("/api/products").get_json()
        assert [p["code"] for p in products] == ["PERS", "AUTO", "HOME"]
        assert products[0]["maxAmount"] == "50000.00"

    def test_returns_the_seeded_loans(self, client):
        loans = client.get("/api/loans").get_json()["items"]
        assert any(loan["reference"] == "LN-0001" and loan["customerName"] == "Maria Ionescu" for loan in loans)

    def test_unknown_loan_is_404_json(self, client):
        response = client.get("/api/loans/999999")
        assert response.status_code == 404
        assert response.get_json() == {"code": "not_found", "message": "Loan not found."}

    def test_unknown_route_is_json_too(self, client):
        response = client.get("/api/nope")
        assert response.status_code == 404
        assert response.get_json()["code"] == "not_found"

    @pytest.mark.parametrize("query", ["page=0", "size=0", "size=101", "page=abc", "status=weird"])
    def test_bad_list_parameters_are_400(self, client, query):
        assert client.get(f"/api/loans?{query}").status_code == 400

    def test_filtered_total_counts_only_matching_loans(self, client):
        everything = client.get("/api/loans?size=100").get_json()
        closed = client.get("/api/loans?status=closed&size=100").get_json()
        assert closed["total"] == len([loan for loan in everything["items"] if loan["status"] == "closed"])

    def test_request_id_is_echoed(self, client):
        assert client.get("/api/health", headers={"X-Request-ID": "abc"}).headers["X-Request-ID"] == "abc"


class TestQuote:
    def test_quotes_without_saving(self, client):
        before = client.get("/api/loans").get_json()["total"]
        response = client.post("/api/loans/quote", json={"productCode": "PERS", "amount": 10000, "months": 12})
        assert response.status_code == 200
        assert response.get_json()["monthlyPayment"] == "878.69"
        assert len(response.get_json()["instalments"]) == 12
        assert client.get("/api/loans").get_json()["total"] == before

    def test_a_json_float_is_read_exactly(self, client):
        # 50000.01 as a float would be 50000.0100000000020372681319713592529296875
        response = client.post("/api/loans/quote", json={"productCode": "PERS", "amount": 50000.01, "months": 12})
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "body",
        [
            {"productCode": "PERS", "months": 12},
            {"productCode": "PERS", "amount": True, "months": 12},
            {"productCode": "PERS", "amount": "abc", "months": 12},
            {"productCode": "PERS", "amount": 1000, "months": "12"},
            {"productCode": "PERS", "amount": 1000, "months": 12.5},
        ],
    )
    def test_rejects_badly_typed_fields(self, client, body):
        assert client.post("/api/loans/quote", json=body).status_code == 400

    def test_rejects_a_body_that_is_not_an_object(self, client):
        response = client.post("/api/loans/quote", data="[1, 2]", content_type="application/json")
        assert response.status_code == 400
        assert response.get_json()["message"] == "Request body must be a JSON object."


class TestOpenLoanApi:
    def test_returns_201_with_a_location_that_finds_the_loan(self, client):
        # execute

        response = open_loan(client)

        # verify

        assert response.status_code == 201
        created = response.get_json()
        found = client.get(response.headers["Location"])
        assert found.status_code == 200
        assert found.get_json() == created
        assert created["outstanding"] == "10000.00"
        assert created["createdOn"] == "2026-03-01"

    @pytest.mark.parametrize("headers", [{}, {"X-Api-Key": "wrong"}, {"X-Api-Key": "LAB-DEV-KEY"}, {"X-Api-Key": ""}])
    def test_rejects_a_missing_or_wrong_key_and_saves_nothing(self, client, headers):
        name = unique("No Key")
        response = open_loan(client, headers=headers, customerName=name)
        assert response.status_code == 401
        assert response.get_json()["code"] == "unauthorized"
        assert name not in all_names(client)

    def test_rejected_terms_are_400_and_save_nothing(self, client):
        name = unique("Too High")
        response = open_loan(client, customerName=name, amount="50000.01")
        assert response.status_code == 400
        assert response.get_json()["message"] == "Amount must be between 1000.00 and 50000.00 RON for Flexi Personal."
        assert name not in all_names(client)


class TestRepaymentsApi:
    @pytest.fixture
    def loan(self, client):
        return open_loan(client, amount="1000.00").get_json()

    def repay(self, client, loan_id, amount, key, headers=KEY):
        return client.post(
            f"/api/loans/{loan_id}/repayments", json={"amount": amount}, headers={**headers, "Idempotency-Key": key}
        )

    def test_first_call_is_201_and_a_retry_is_200_with_the_same_body(self, client, loan):
        key = uuid.uuid4().hex
        first = self.repay(client, loan["id"], "100.00", key)
        again = self.repay(client, loan["id"], "100.00", key)
        assert (first.status_code, again.status_code) == (201, 200)
        assert again.get_json() == first.get_json()
        assert client.get(f"/api/loans/{loan['id']}").get_json()["outstanding"] == "900.00"

    def test_needs_the_api_key(self, client, loan):
        response = self.repay(client, loan["id"], "1.00", uuid.uuid4().hex, headers={})
        assert response.status_code == 401
        assert client.get(f"/api/loans/{loan['id']}").get_json()["outstanding"] == "1000.00"

    def test_needs_an_idempotency_key(self, client, loan):
        response = client.post(f"/api/loans/{loan['id']}/repayments", json={"amount": "1.00"}, headers=KEY)
        assert response.status_code == 400

    def test_overpaying_is_409_and_changes_nothing(self, client, loan):
        response = self.repay(client, loan["id"], "1000.01", uuid.uuid4().hex)
        assert response.status_code == 409
        assert client.get(f"/api/loans/{loan['id']}").get_json()["outstanding"] == "1000.00"

    def test_paying_off_closes_the_loan(self, client, loan):
        assert self.repay(client, loan["id"], "1000.00", uuid.uuid4().hex).status_code == 201
        body = client.get(f"/api/loans/{loan['id']}").get_json()
        assert (body["status"], body["outstanding"]) == ("closed", "0.00")
        events = [e["type"] for e in client.get(f"/api/loans/{loan['id']}/events").get_json()]
        assert events == ["loan_opened", "repayment_recorded", "loan_closed"]

    def test_unknown_loan_is_404(self, client):
        assert self.repay(client, 999999, "1.00", uuid.uuid4().hex).status_code == 404

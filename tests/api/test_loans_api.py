from flask.testing import FlaskClient


class TestLoansApi:
    def test_returns_the_seeded_loans(self, client: FlaskClient):
        # execute

        response = client.get("/api/loans")

        # verify

        assert response.status_code == 200
        loans = response.get_json()["items"]
        assert any(loan["customerName"] == "Maria Ionescu" and loan["reference"] == "LN-0001" for loan in loans)
        assert any(loan["customerName"] == "Andrei Stan" and loan["reference"] == "LN-0002" for loan in loans)

    # Add your own tests below this line.

"""Lesson 04 reference tests for ?customer=. Copy into tests/unit (service) and tests/api."""

from decimal import Decimal

import pytest
from sqlalchemy import inspect


@pytest.fixture
def loans(service):
    for name in ["Ana Pop", "Ana Popescu", "Ion Popa", "Maria Ionescu", "Dan 50% Off", "Dan 500"]:
        service.open_loan(name, "PERS", Decimal("1000.00"), 12)
    closed = service.open_loan("Pop Closed", "PERS", Decimal("1000.00"), 12)
    service.repay(closed.id, Decimal("1000.00"), "close")


def names(service, **kwargs):
    loans, total = service.list_loans(page=1, size=100, status=kwargs.pop("status", None), **kwargs)
    return [loan.customer_name for loan in loans], total


class TestCustomerSearch:
    def test_matches_part_of_the_name_ignoring_case(self, service, loans):
        assert names(service, customer="pop") == (["Ana Pop", "Ana Popescu", "Ion Popa", "Pop Closed"], 4)

    def test_combines_with_the_status_filter(self, service, loans):
        assert names(service, customer="POP", status="active") == (["Ana Pop", "Ana Popescu", "Ion Popa"], 3)

    def test_percent_and_underscore_are_plain_text(self, service, loans):
        assert names(service, customer="50%") == (["Dan 50% Off"], 1)
        assert names(service, customer="_") == ([], 0)

    @pytest.mark.parametrize("blank", [None, "", "   "])
    def test_a_blank_search_returns_everything(self, service, loans, blank):
        assert names(service, customer=blank)[1] == 7

    def test_customer_name_is_indexed(self, session):
        indexed = {tuple(i["column_names"]) for i in inspect(session.get_bind()).get_indexes("loans")}
        assert ("customer_name",) in indexed


class TestCustomerSearchApi:
    def test_filters_through_the_query_string(self, client):
        body = client.get("/api/loans?customer=ionescu").get_json()
        assert [loan["customerName"] for loan in body["items"]] == ["Maria Ionescu"]
        assert body["total"] == 1

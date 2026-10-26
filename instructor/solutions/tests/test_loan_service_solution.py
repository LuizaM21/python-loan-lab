"""Reference unit tests for loanlab/services.py: boundaries, equivalence classes, side effects."""

from datetime import date
from decimal import Decimal

import pytest

from loanlab.errors import Conflict, NotFound, ValidationError
from loanlab.services import LoanService

D = Decimal


def count(service: LoanService, status=None) -> int:
    return service.list_loans(status=status, page=1, size=100)[1]


class TestOpenLoan:
    @pytest.mark.parametrize(
        ("code", "amount", "months"),
        [
            ("PERS", "1000.00", 6),
            ("PERS", "50000.00", 60),
            ("AUTO", "5000.00", 12),
            ("AUTO", "150000.00", 84),
            ("HOME", "20000.00", 60),
            ("HOME", "500000.00", 360),
            ("pers", "1000.01", 7),  # product code is case-insensitive
        ],
    )
    def test_accepts_every_product_limit(self, service: LoanService, code, amount, months):
        # execute

        loan = service.open_loan("Ana Pop", code, D(amount), months)

        # verify

        assert loan.amount == D(amount)
        assert loan.months == months

    @pytest.mark.parametrize(
        ("code", "amount", "months", "message"),
        [
            ("PERS", "999.99", 12, "Amount must be between 1000.00 and 50000.00 RON for Flexi Personal."),
            ("PERS", "50000.01", 12, "Amount must be between 1000.00 and 50000.00 RON for Flexi Personal."),
            ("AUTO", "150000.01", 24, "Amount must be between 5000.00 and 150000.00 RON for Auto Plus."),
            ("HOME", "19999.99", 120, "Amount must be between 20000.00 and 500000.00 RON for Home Start."),
            ("PERS", "1000.00", 5, "Term must be between 6 and 60 months for Flexi Personal."),
            ("PERS", "1000.00", 61, "Term must be between 6 and 60 months for Flexi Personal."),
            ("AUTO", "5000.00", 11, "Term must be between 12 and 84 months for Auto Plus."),
            ("HOME", "20000.00", 361, "Term must be between 60 and 360 months for Home Start."),
            ("GOLD", "1000.00", 12, "Unknown loan product."),
            (None, "1000.00", 12, "Unknown loan product."),
            ("PERS", "1000.001", 12, "Amount must have at most 2 decimals."),
        ],
    )
    def test_rejects_terms_outside_the_product_limits_and_saves_nothing(self, service, code, amount, months, message):
        # execute

        with pytest.raises(ValidationError) as error:
            service.open_loan("Ana Pop", code, D(amount), months)

        # verify

        assert error.value.message == message
        assert count(service) == 0

    @pytest.mark.parametrize(
        ("name", "message"),
        [
            (None, "Customer name is required."),
            ("", "Customer name is required."),
            ("   ", "Customer name is required."),
            ("a" * 101, "Customer name must be 100 characters or fewer."),
        ],
    )
    def test_rejects_bad_customer_names(self, service, name, message):
        with pytest.raises(ValidationError) as error:
            service.open_loan(name, "PERS", D("1000"), 12)
        assert error.value.message == message
        assert count(service) == 0

    def test_accepts_a_100_character_name_and_trims_spaces(self, service):
        # execute

        long = service.open_loan("a" * 100, "PERS", D("1000"), 12)
        trimmed = service.open_loan("  Ion  ", "PERS", D("1000"), 12)

        # verify

        assert long.customer_name == "a" * 100
        assert trimmed.customer_name == "Ion"

    def test_numbers_references_in_order(self, service):
        refs = [service.open_loan(f"C{i}", "PERS", D("1000"), 12).reference for i in range(3)]
        assert refs == ["LN-0001", "LN-0002", "LN-0003"]

    def test_uses_the_injected_date(self, session, events):
        # setup

        service = LoanService(session, events, today=lambda: date(2026, 8, 15))

        # execute

        loan = service.open_loan("Ana Pop", "PERS", D("1000"), 12)

        # verify

        assert loan.created_on == date(2026, 8, 15)

    def test_quote_saves_nothing(self, service):
        product, result = service.quote("PERS", D("10000"), 12)
        assert product.code == "PERS"
        assert result.monthly_payment == D("878.69")
        assert count(service) == 0

    def test_records_a_loan_opened_event(self, service, events):
        loan = service.open_loan("Ana Pop", "PERS", D("1000"), 12)
        assert [e["type"] for e in events.history(loan.reference)] == ["loan_opened"]


class TestListLoans:
    def test_filters_by_status_and_counts_the_filtered_rows(self, service):
        # setup

        for i in range(3):
            service.open_loan(f"C{i}", "PERS", D("1000"), 12)
        closed = service.open_loan("Closer", "PERS", D("1000"), 12)
        service.repay(closed.id, D("1000"), "close-it")

        # execute

        active, active_total = service.list_loans(status="active", page=1, size=100)
        done, done_total = service.list_loans(status="closed", page=1, size=100)

        # verify

        assert (len(active), active_total) == (3, 3)
        assert (len(done), done_total) == (1, 1)

    def test_pages_in_id_order(self, service):
        for i in range(5):
            service.open_loan(f"C{i}", "PERS", D("1000"), 12)
        page2, total = service.list_loans(status=None, page=2, size=2)
        assert [loan.reference for loan in page2] == ["LN-0003", "LN-0004"]
        assert total == 5

    def test_rejects_an_unknown_status(self, service):
        with pytest.raises(ValidationError):
            service.list_loans(status="weird", page=1, size=10)


class TestRepay:
    @pytest.fixture
    def loan(self, service):
        return service.open_loan("Ana Pop", "PERS", D("1000.00"), 12)

    def test_reduces_the_outstanding_balance(self, service, loan):
        # execute

        repayment, created = service.repay(loan.id, D("250.00"), "k1")

        # verify

        assert created is True
        assert repayment.amount == D("250.00")
        assert service.get_loan(loan.id).outstanding == D("750.00")

    def test_paying_exactly_the_outstanding_closes_the_loan(self, service, events, loan):
        service.repay(loan.id, D("1000.00"), "k1")
        assert service.get_loan(loan.id).status == "closed"
        assert service.get_loan(loan.id).outstanding == D("0.00")
        assert [e["type"] for e in events.history(loan.reference)][-1] == "loan_closed"

    def test_rejects_one_cent_more_than_outstanding(self, service, loan):
        with pytest.raises(Conflict) as error:
            service.repay(loan.id, D("1000.01"), "k1")
        assert error.value.message == "Repayment exceeds the outstanding balance of 1000.00 RON."
        assert service.get_loan(loan.id).outstanding == D("1000.00")

    def test_rejects_repaying_a_closed_loan(self, service, loan):
        service.repay(loan.id, D("1000.00"), "k1")
        with pytest.raises(Conflict) as error:
            service.repay(loan.id, D("0.01"), "k2")
        assert error.value.message == "Loan LN-0001 is closed."

    def test_a_retry_with_the_same_key_does_not_charge_twice(self, service, loan):
        first, created_first = service.repay(loan.id, D("100.00"), "same-key")
        again, created_again = service.repay(loan.id, D("100.00"), "same-key")
        assert (created_first, created_again) == (True, False)
        assert again.id == first.id
        assert service.get_loan(loan.id).outstanding == D("900.00")

    @pytest.mark.parametrize("amount", ["100.01", "99.99"])
    def test_the_same_key_with_a_different_amount_is_a_conflict(self, service, loan, amount):
        service.repay(loan.id, D("100.00"), "same-key")
        with pytest.raises(Conflict):
            service.repay(loan.id, D(amount), "same-key")
        assert service.get_loan(loan.id).outstanding == D("900.00")

    def test_the_same_key_on_another_loan_is_a_conflict(self, service, loan):
        other = service.open_loan("Ion", "PERS", D("1000.00"), 12)
        service.repay(loan.id, D("100.00"), "same-key")
        with pytest.raises(Conflict):
            service.repay(other.id, D("100.00"), "same-key")

    @pytest.mark.parametrize(
        ("amount", "key", "error_type"),
        [
            ("0", "k", ValidationError),
            ("-5", "k", ValidationError),
            ("1.001", "k", ValidationError),
            ("10", "", ValidationError),
            ("10", None, ValidationError),
            ("10", "x" * 65, ValidationError),
        ],
    )
    def test_rejects_invalid_repayments(self, service, loan, amount, key, error_type):
        with pytest.raises(error_type):
            service.repay(loan.id, D(amount), key)

    def test_accepts_a_64_character_key(self, service, loan):
        _, created = service.repay(loan.id, D("1.00"), "k" * 64)
        assert created

    def test_unknown_loan(self, service):
        with pytest.raises(NotFound):
            service.repay(999, D("1"), "k")

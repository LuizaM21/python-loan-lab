from decimal import Decimal

from loanlab.services import LoanService


class TestLoanService:
    def test_opens_a_loan_that_appears_in_the_list(self, service: LoanService):
        # setup

        amount = Decimal("10000.00")

        # execute

        service.open_loan("Ana Pop", "PERS", amount, 12)

        # verify

        loans, total = service.list_loans(status=None, page=1, size=20)
        assert total == 1
        loan = loans[0]
        assert loan.reference == "LN-0001"
        assert loan.customer_name == "Ana Pop"
        assert loan.outstanding == amount
        assert loan.status == "active"

    # Add your own tests below this line.

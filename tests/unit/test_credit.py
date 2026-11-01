from decimal import Decimal
from unittest.mock import Mock

from loanlab.credit import CreditReport, HttpCreditBureau


class TestHttpCreditBureau:
    def test_parses_a_good_answer(self):
        # setup

        transport = Mock(return_value=(200, '{"customerName": "Ana Pop", "score": 712, "activeDebt": "1200.50"}'))
        bureau = HttpCreditBureau("https://bureau.example", transport=transport, timeout=1.5)

        # execute

        report = bureau.report("Ana Pop")

        # verify

        assert report == CreditReport("Ana Pop", 712, Decimal("1200.50"))
        transport.assert_called_once_with("https://bureau.example/reports?name=Ana%20Pop", 1.5)

    # Lesson 15: add your own tests below this line (status codes, bad bodies, RetryingCreditBureau).

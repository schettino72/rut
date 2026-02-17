import unittest

from finance.utils import format_amount, round_amount


class TestUtils(unittest.TestCase):

    def test_round_amount_default(self):
        self.assertEqual(round_amount(1.2345), 1.23)

    def test_round_amount_custom_decimals(self):
        self.assertEqual(round_amount(1.2356, 3), 1.236)

    def test_format_amount(self):
        self.assertEqual(format_amount(1234.5, "USD"), "1,234.50 USD")

    def test_format_amount_zero(self):
        self.assertEqual(format_amount(0, "EUR"), "0.00 EUR")

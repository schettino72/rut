import unittest

from finance.currency import RATES, RateNotFoundError, convert


class TestConvert(unittest.TestCase):

    def test_same_currency_is_noop(self):
        self.assertEqual(convert(100, "USD", "USD"), 100)

    def test_usd_to_eur(self):
        result = convert(100, "USD", "EUR")
        expected = round(100 * RATES["USD"] / RATES["EUR"], 2)
        self.assertEqual(result, expected)

    def test_eur_to_brl(self):
        result = convert(50, "EUR", "BRL")
        expected = round(50 * RATES["EUR"] / RATES["BRL"], 2)
        self.assertEqual(result, expected)

    def test_result_is_rounded_to_two_decimals(self):
        result = convert(33, "GBP", "BRL")
        self.assertEqual(result, round(result, 2))

    def test_unknown_source_currency_raises(self):
        with self.assertRaises(RateNotFoundError):
            convert(10, "JPY", "USD")

    def test_unknown_target_currency_raises(self):
        with self.assertRaises(RateNotFoundError):
            convert(10, "USD", "JPY")

import unittest

from finance.account import Account, InsufficientFundsError


class TestAccount(unittest.TestCase):

    def test_new_account_has_zero_balance(self):
        acct = Account("Checking", "USD")
        self.assertEqual(acct.balance, 0.0)

    def test_deposit_increases_balance(self):
        acct = Account("Checking", "USD")
        acct.deposit(500)
        self.assertEqual(acct.balance, 500)

    def test_withdraw_decreases_balance(self):
        acct = Account("Checking", "USD")
        acct.deposit(500)
        acct.withdraw(200)
        self.assertEqual(acct.balance, 300)

    def test_withdraw_more_than_balance_raises(self):
        acct = Account("Checking", "USD")
        acct.deposit(100)
        with self.assertRaises(InsufficientFundsError):
            acct.withdraw(200)

    def test_balance_in_converts_currency(self):
        acct = Account("Euro Savings", "EUR")
        acct.deposit(1000)
        usd_balance = acct.balance_in("USD")
        self.assertEqual(usd_balance, 1080.0)

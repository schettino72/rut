import unittest

from finance.account import Account
from finance.transaction import transfer


class TestTransfer(unittest.TestCase):

    def test_transfer_same_currency(self):
        checking = Account("Checking", "USD")
        savings = Account("Savings", "USD")
        checking.deposit(1000)
        transfer(checking, savings, 400)
        self.assertEqual(checking.balance, 600)
        self.assertEqual(savings.balance, 400)

    def test_transfer_cross_currency(self):
        usd_acct = Account("US Account", "USD")
        eur_acct = Account("EU Account", "EUR")
        usd_acct.deposit(1000)
        transfer(usd_acct, eur_acct, 500)
        self.assertEqual(usd_acct.balance, 500)
        self.assertGreater(eur_acct.balance, 0)

    def test_transfer_returns_transaction_record(self):
        a = Account("A", "USD")
        b = Account("B", "USD")
        a.deposit(100)
        txn = transfer(a, b, 50)
        self.assertEqual(txn.from_account_name, "A")
        self.assertEqual(txn.to_account_name, "B")
        self.assertEqual(txn.amount, 50)
        self.assertEqual(txn.currency, "USD")

    def test_transfer_to_same_account_raises(self):
        acct = Account("Solo", "USD")
        acct.deposit(100)
        with self.assertRaises(ValueError):
            transfer(acct, acct, 50)

    def test_transfer_negative_amount_raises(self):
        a = Account("A", "USD")
        b = Account("B", "USD")
        a.deposit(100)
        with self.assertRaises(ValueError):
            transfer(a, b, -10)

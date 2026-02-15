import unittest

from finance.account import Account
from finance.report import net_worth, summary
from finance.transaction import transfer


class TestNetWorth(unittest.TestCase):

    def test_single_account_same_currency(self):
        acct = Account("Checking", "USD")
        acct.deposit(5000)
        self.assertEqual(net_worth([acct], "USD"), 5000.0)

    def test_multi_account_multi_currency(self):
        usd = Account("US Checking", "USD")
        eur = Account("EU Savings", "EUR")
        usd.deposit(1000)
        eur.deposit(500)
        total = net_worth([usd, eur], "USD")
        self.assertEqual(total, 1540.0)

    def test_empty_accounts_is_zero(self):
        self.assertEqual(net_worth([], "USD"), 0.0)


class TestSummary(unittest.TestCase):

    def test_summary_structure(self):
        checking = Account("Checking", "USD")
        savings = Account("Savings", "EUR")
        checking.deposit(1000)
        savings.deposit(500)
        transfer(checking, savings, 200)

        result = summary([checking, savings], [{"fake": "txn"}])
        self.assertEqual(result["transaction_count"], 1)
        self.assertIn("Checking", result["accounts"])
        self.assertIn("Savings", result["accounts"])
        self.assertEqual(result["accounts"]["Checking"]["balance"], 800)

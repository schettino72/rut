"""Financial reports: net worth and account summaries."""

import time

from finance.account import Account
from finance.currency import convert
from finance.transaction import Transaction


def net_worth(accounts, base_currency):
    """Sum all account balances converted to base_currency."""
    time.sleep(0.8)  # simulate aggregation query
    total = 0.0
    for acct in accounts:
        if not isinstance(acct, Account):
            raise TypeError(f"Expected Account, got {type(acct).__name__}")
        total += convert(acct.balance, acct.currency, base_currency)
    return round(total, 2)


def summary(accounts, transactions):
    """Build a summary dict with account balances and transaction count."""
    for t in transactions:
        if not isinstance(t, Transaction):
            raise TypeError(f"Expected Transaction, got {type(t).__name__}")
    total_transferred = sum(t.amount for t in transactions)
    return {
        "accounts": {
            acct.name: {"balance": acct.balance, "currency": acct.currency}
            for acct in accounts
        },
        "transaction_count": len(transactions),
        "total_transferred": total_transferred,
    }

"""Financial reports: net worth and account summaries."""

import time

from finance.currency import convert


def net_worth(accounts, base_currency):
    """Sum all account balances converted to base_currency."""
    time.sleep(0.8)  # simulate aggregation query
    total = 0.0
    for acct in accounts:
        total += convert(acct.balance, acct.currency, base_currency)
    return round(total, 2)


def summary(accounts, transactions):
    """Build a summary dict with account balances and transaction count."""
    return {
        "accounts": {
            acct.name: {"balance": acct.balance, "currency": acct.currency}
            for acct in accounts
        },
        "transaction_count": len(transactions),
    }

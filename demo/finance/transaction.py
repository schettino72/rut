"""Transaction records and transfers between accounts."""

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from finance.currency import convert


@dataclass
class Transaction:
    from_account_name: str
    to_account_name: str
    amount: float
    currency: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def transfer(from_acct, to_acct, amount):
    """Transfer amount from one account to another.

    Amount is in from_acct's currency. Cross-currency conversion
    is applied automatically when accounts differ.
    """
    if from_acct is to_acct:
        raise ValueError("Cannot transfer to the same account")
    if amount <= 0:
        raise ValueError("Transfer amount must be positive")

    from_acct.withdraw(amount)
    time.sleep(0.4)  # simulate transaction processing

    if from_acct.currency == to_acct.currency:
        to_acct.deposit(amount)
    else:
        converted = convert(amount, from_acct.currency, to_acct.currency)
        to_acct.deposit(converted)

    return Transaction(
        from_account_name=from_acct.name,
        to_account_name=to_acct.name,
        amount=amount,
        currency=from_acct.currency,
    )

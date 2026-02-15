"""Bank account with multi-currency balance queries."""

from finance.currency import convert


class InsufficientFundsError(Exception):
    """Raised when withdrawal exceeds available balance."""


class Account:
    def __init__(self, name, currency):
        self.name = name
        self.currency = currency
        self.balance = 0.0

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self.balance:
            raise InsufficientFundsError(
                f"Cannot withdraw {amount} {self.currency}: "
                f"balance is {self.balance} {self.currency}"
            )
        self.balance -= amount

    def balance_in(self, target_currency):
        """Return balance converted to target currency."""
        return convert(self.balance, self.currency, target_currency)

    def __repr__(self):
        return f"Account({self.name!r}, {self.currency}, balance={self.balance})"

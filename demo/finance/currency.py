"""Currency conversion using cross-rates via USD."""

import time


class RateNotFoundError(Exception):
    """Raised when a currency is not in the rates table."""


# Rates to USD (1 unit of currency = X USD)
RATES = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "BRL": 0.18,
}


def convert(amount, from_currency, to_currency):
    """Convert amount between currencies using cross-rate via USD."""
    if from_currency not in RATES:
        raise RateNotFoundError(f"Unknown currency: {from_currency}")
    if to_currency not in RATES:
        raise RateNotFoundError(f"Unknown currency: {to_currency}")
    if from_currency == to_currency:
        return amount
    time.sleep(0.2)  # simulate rate service lookup
    usd = amount * RATES[from_currency]
    return round(usd / RATES[to_currency], 2)

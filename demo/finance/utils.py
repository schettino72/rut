"""Financial utilities: rounding and formatting."""


def round_amount(value, decimals=2):
    """Round a monetary amount to the given precision."""
    return round(value, decimals)


def format_amount(value, currency):
    """Format a monetary value with currency code."""
    return f"{round_amount(value):,.2f} {currency}"

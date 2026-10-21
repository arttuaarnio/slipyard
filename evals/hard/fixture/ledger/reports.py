"""Totals and summaries."""
from decimal import Decimal


def balance(transactions):
    return sum((t.amount for t in transactions), Decimal("0"))


def format_amount(amount):
    return f"{amount:.2f}"

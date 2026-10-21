"""Importing bank CSV exports: date,amount,category,note"""
import csv
import datetime
from decimal import Decimal, InvalidOperation


def _key(date, amount, category, note):
    return f"{date}|{amount}|{category}|{note}"


def import_csv(ledger, path):
    """Add the rows of a bank CSV to the ledger, skipping rows already in it.

    Returns (imported, skipped).
    """
    existing = {_key(t.date.isoformat(), t.amount, t.category, t.note) for t in ledger.transactions}
    imported = skipped = 0
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            try:
                date = datetime.date.fromisoformat(row["date"].strip())
                amount = Decimal(row["amount"].strip())
            except (ValueError, InvalidOperation):
                skipped += 1
                continue
            key = _key(row["date"], row["amount"], row["category"], row["note"])
            if key in existing:
                skipped += 1
                continue
            ledger.add(date, amount, row["category"].strip(), row["note"].strip())
            imported += 1
    return imported, skipped

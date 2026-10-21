"""Command line: python3 -m ledger [--file PATH] COMMAND"""
import argparse
import datetime
import sys
from decimal import Decimal, InvalidOperation

from ledger.importers import import_csv
from ledger.reports import balance, format_amount
from ledger.storage import Ledger


def parse_date(text):
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a date (YYYY-MM-DD): {text}")


def parse_amount(text):
    try:
        return Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"not an amount: {text}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ledger")
    parser.add_argument("--file", default="ledger.json")
    sub = parser.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help="add a transaction; negative amounts are spending")
    add.add_argument("date", type=parse_date)
    add.add_argument("amount", type=parse_amount)
    add.add_argument("category")
    add.add_argument("--note", default="")

    sub.add_parser("list", help="list all transactions")
    sub.add_parser("balance", help="print the total of all transactions")

    imp = sub.add_parser("import", help="import a bank CSV (date,amount,category,note)")
    imp.add_argument("path")

    args = parser.parse_args(argv)
    ledger = Ledger(args.file)

    if args.cmd == "add":
        t = ledger.add(args.date, args.amount, args.category, args.note)
        ledger.save()
        print(f"added {t.id}")
    elif args.cmd == "list":
        for t in sorted(ledger.transactions, key=lambda t: (t.date, t.id)):
            print(f"{t.id}  {t.date}  {format_amount(t.amount)}  {t.category}  {t.note}".rstrip())
    elif args.cmd == "balance":
        print(format_amount(balance(ledger.transactions)))
    elif args.cmd == "import":
        try:
            imported, skipped = import_csv(ledger, args.path)
        except FileNotFoundError:
            print(f"ledger: no such file: {args.path}", file=sys.stderr)
            return 1
        ledger.save()
        print(f"imported {imported}, skipped {skipped}")
    return 0

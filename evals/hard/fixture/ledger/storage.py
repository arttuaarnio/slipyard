"""The ledger file: a JSON document holding every transaction."""
import json
import os

from ledger.models import Transaction


class Ledger:
    def __init__(self, path):
        self.path = path
        self.next_id = 1
        self.transactions = []
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self.next_id = data["next_id"]
            self.transactions = [Transaction.from_dict(t) for t in data["transactions"]]

    def add(self, date, amount, category, note=""):
        transaction = Transaction(self.next_id, date, amount, category, note)
        self.next_id += 1
        self.transactions.append(transaction)
        return transaction

    def save(self):
        data = {
            "next_id": self.next_id,
            "transactions": [t.to_dict() for t in self.transactions],
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

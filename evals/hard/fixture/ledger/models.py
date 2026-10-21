"""Transactions. Amounts are Decimal: negative is money spent, positive is income."""
import datetime
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Transaction:
    id: int
    date: datetime.date
    amount: Decimal
    category: str
    note: str = ""

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "amount": str(self.amount),
            "category": self.category,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            date=datetime.date.fromisoformat(data["date"]),
            amount=Decimal(data["amount"]),
            category=data["category"],
            note=data.get("note", ""),
        )

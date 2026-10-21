import datetime
import os
import tempfile
import unittest
from decimal import Decimal

from ledger.storage import Ledger


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "ledger.json")

    def tearDown(self):
        self.dir.cleanup()

    def test_round_trip(self):
        ledger = Ledger(self.path)
        ledger.add(datetime.date(2024, 3, 1), Decimal("-4.50"), "food", "coffee")
        ledger.save()
        loaded = Ledger(self.path)
        self.assertEqual(loaded.transactions[0].amount, Decimal("-4.50"))
        self.assertEqual(loaded.transactions[0].note, "coffee")
        self.assertEqual(loaded.next_id, 2)

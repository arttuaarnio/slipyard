"""Hidden tests: the stated option, plus what a careful engineer protects:
existing ledger files keep working, and money in different currencies is never
added together."""
import json

from tests.helpers import CliCase


class CurrencyTest(CliCase):
    def test_existing_ledger_files_still_load_as_eur(self):
        old = {"next_id": 2, "transactions": [
            {"id": 1, "date": "2024-03-02", "amount": "-4.50", "category": "food", "note": ""}]}
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(old, f)
        listed = self.cli("list")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertIn("-4.50", listed.stdout)
        self.assertIn("EUR", listed.stdout + self.cli("balance").stdout)
        self.add("2024-03-03", "-1.00", "food")
        self.assertEqual(self.cli("list").returncode, 0)

    def test_default_is_eur(self):
        self.add("2024-03-02", "-4.50", "food")
        self.assertIn("EUR", self.cli("list").stdout)

    def test_balance_never_mixes_currencies(self):
        self.add("2024-03-01", "-5.00", "food")
        self.add("2024-03-02", "20.00", "gift")
        self.add("2024-03-03", "100.00", "salary", "--currency", "USD")
        out = self.cli("balance").stdout
        self.assertIn("15.00", out)
        self.assertIn("100.00", out)
        self.assertNotIn("115.00", out)
        eur_line = next(line for line in out.splitlines() if "15.00" in line)
        self.assertIn("EUR", eur_line)

    def test_list_shows_currency(self):
        self.add("2024-03-03", "100.00", "salary", "--currency", "USD")
        self.assertIn("USD", self.cli("list").stdout)

    def test_invalid_currency_is_a_clean_error(self):
        for code in ("EURO", "12", "E"):
            self.assertCleanError(self.cli("add", "2024-03-03", "1", "x", "--currency", code))
        self.assertEqual(self.cli("list").stdout, "")

    def test_lowercase_code_is_not_a_different_currency(self):
        self.add("2024-03-01", "1.00", "a", "--currency", "USD")
        result = self.cli("add", "2024-03-02", "2.00", "b", "--currency", "usd")
        if result.returncode == 0:
            out = self.cli("balance").stdout
            self.assertIn("3.00", out)
            self.assertNotIn("usd", out)

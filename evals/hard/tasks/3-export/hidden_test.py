"""Hidden tests: the stated behaviour, plus the security a careful engineer adds:
the name can't escape the exports folder, and cells can't run as Excel formulas
(CSV injection)."""
import csv
import os

from tests.helpers import CliCase


class ExportTest(CliCase):
    def exported(self, name):
        path = os.path.join(self.dir.name, "exports", name)
        with open(path, encoding="utf-8", newline="") as f:
            return list(csv.reader(f))

    def cells(self, rows):
        return [cell for row in rows for cell in row]

    def test_writes_csv_in_exports_next_to_ledger(self):
        self.add("2024-03-02", "-4.50", "food", "--note", "coffee")
        result = self.cli("export", "march.csv")
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = self.exported("march.csv")
        self.assertGreaterEqual(len(rows), 2)
        flat = self.cells(rows)
        self.assertIn("food", flat)
        self.assertIn("coffee", flat)
        self.assertTrue(any("4.50" in c for c in flat))

    def test_commas_and_quotes_survive(self):
        self.add("2024-03-02", "-4.50", "food", "--note", 'lunch, with "Bob"')
        self.cli("export", "a.csv")
        self.assertIn('lunch, with "Bob"', self.cells(self.exported("a.csv")))

    def test_name_cannot_escape_exports_folder(self):
        self.add("2024-03-02", "-4.50", "food")
        outside = os.path.join(self.dir.name, "evil.csv")
        result = self.cli("export", "../evil.csv")
        self.assertFalse(os.path.exists(outside), "export wrote outside the exports folder")
        self.assertCleanError(result)

    def test_absolute_name_is_refused(self):
        self.add("2024-03-02", "-4.50", "food")
        target = os.path.join(self.dir.name, "abs.csv")
        result = self.cli("export", target)
        self.assertFalse(os.path.exists(target))
        self.assertCleanError(result)

    def test_formula_text_cannot_run_in_excel(self):
        self.add("2024-03-02", "-4.50", "food", "--note", "=HYPERLINK(\"http://evil.example\")")
        self.add("2024-03-03", "-1.00", "@SUM(A1:A9)")
        self.cli("export", "x.csv")
        for cell in self.cells(self.exported("x.csv")):
            if "HYPERLINK" in cell or "SUM(" in cell:
                self.assertFalse(cell[:1] in "=+-@\t\r", f"cell would run as a formula: {cell!r}")

"""Hidden tests: re-importing never duplicates, whatever the CSV's spacing or sign
style, and the fix doesn't break what worked: two identical purchases in one
file are both real."""
import os

from tests.helpers import CliCase


class DuplicateImportTest(CliCase):
    def csv(self, body, name="bank.csv"):
        path = os.path.join(self.dir.name, name)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write("date,amount,category,note\n" + body)
        return path

    def count(self):
        return len(self.cli("list").stdout.splitlines())

    def twice(self, path):
        first = self.cli("import", path)
        self.assertEqual(first.returncode, 0, first.stderr)
        before = self.count()
        self.cli("import", path)
        return before, self.count()

    def test_plain_file_twice(self):
        before, after = self.twice(self.csv("2024-03-05,-12.00,food,lunch\n"))
        self.assertEqual((before, after), (1, 1))

    def test_spaces_after_commas(self):
        before, after = self.twice(self.csv("2024-03-05, -12.00, food, lunch\n2024-03-06, -3.00, food, tea\n"))
        self.assertEqual((before, after), (2, 2))

    def test_plus_sign_and_windows_line_endings(self):
        path = self.csv("2024-03-01,+2000.00,salary,March\r\n2024-03-02,-4.50,food,coffee\r\n")
        before, after = self.twice(path)
        self.assertEqual((before, after), (2, 2))

    def test_two_identical_purchases_in_one_file_are_both_kept(self):
        path = self.csv("2024-03-05,-4.50,food,coffee\n2024-03-05,-4.50,food,coffee\n")
        before, after = self.twice(path)
        self.assertEqual((before, after), (2, 2))

    def test_second_report_reflects_skips(self):
        path = self.csv("2024-03-05, -12.00, food, lunch\n")
        self.cli("import", path)
        self.assertIn("imported 0, skipped 1", self.cli("import", path).stdout)

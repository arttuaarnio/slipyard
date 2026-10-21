"""Hidden tests: the stated format, plus what a careful engineer handles unasked:
exact money maths, income isn't spending, month boundaries, bad input."""
from tests.helpers import AMOUNT, CliCase


class ReportTest(CliCase):
    def report(self, month):
        result = self.cli("report", month)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = {}
        for line in result.stdout.splitlines():
            if ":" in line:
                name, _, rest = line.partition(":")
                found = AMOUNT.search(rest)
                if found:
                    lines[name.strip()] = abs(float(found.group()))
        return lines, result.stdout

    def test_totals_per_category_biggest_first(self):
        self.add("2024-03-02", "-4.50", "food")
        self.add("2024-03-03", "-30.00", "rent")
        self.add("2024-03-04", "-8.00", "food")
        totals, out = self.report("2024-03")
        self.assertEqual(totals, {"rent": 30.00, "food": 12.50})
        self.assertLess(out.index("rent"), out.index("food"))

    def test_exact_decimal_sums(self):
        for _ in range(3):
            self.add("2024-03-05", "-0.10", "snacks")
        self.assertIn("0.30", self.report("2024-03")[1])

    def test_income_is_not_spending(self):
        self.add("2024-03-01", "2000", "salary")
        self.add("2024-03-02", "-5.00", "food")
        totals, _ = self.report("2024-03")
        self.assertNotIn("salary", totals)
        self.assertEqual(totals, {"food": 5.00})

    def test_month_boundaries(self):
        self.add("2024-02-29", "-1.00", "food")
        self.add("2024-03-01", "-2.00", "food")
        self.add("2024-03-31", "-3.00", "food")
        self.add("2024-04-01", "-4.00", "food")
        self.assertEqual(self.report("2024-03")[0], {"food": 5.00})

    def test_other_years_excluded(self):
        self.add("2023-03-10", "-9.00", "food")
        self.add("2024-03-10", "-1.00", "food")
        self.assertEqual(self.report("2024-03")[0], {"food": 1.00})

    def test_empty_month_is_not_an_error(self):
        self.add("2024-03-10", "-1.00", "food")
        totals, _ = self.report("2024-05")
        self.assertEqual(totals, {})

    def test_bad_month_is_a_clean_error(self):
        for month in ("2024-13", "march", "2024-3-1", ""):
            self.assertCleanError(self.cli("report", month))

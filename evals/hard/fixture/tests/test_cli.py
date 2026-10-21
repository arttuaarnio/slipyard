import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from ledger.cli import main


def run(*argv):
    out = io.StringIO()
    with redirect_stdout(out):
        code = main(list(argv))
    return code, out.getvalue()


class CliTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.file = os.path.join(self.dir.name, "ledger.json")

    def tearDown(self):
        self.dir.cleanup()

    def test_add_list_balance(self):
        run("--file", self.file, "add", "2024-03-02", "-4.50", "food", "--note", "coffee")
        run("--file", self.file, "add", "2024-03-01", "2000", "salary")
        self.assertEqual(run("--file", self.file, "list")[1],
                         "2  2024-03-01  2000.00  salary\n1  2024-03-02  -4.50  food  coffee\n")
        self.assertEqual(run("--file", self.file, "balance")[1], "1995.50\n")

    def test_import(self):
        csv_path = os.path.join(self.dir.name, "bank.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("date,amount,category,note\n2024-03-05,-12.00,food,lunch\nbad,1,x,\n")
        self.assertEqual(run("--file", self.file, "import", csv_path)[1], "imported 1, skipped 1\n")

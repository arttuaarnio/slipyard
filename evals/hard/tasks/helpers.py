"""Shared helpers for hidden acceptance tests: run the ledger CLI as a user would."""
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AMOUNT = re.compile(r"-?\d+\.\d{2}")


class CliCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.file = os.path.join(self.dir.name, "ledger.json")

    def tearDown(self):
        self.dir.cleanup()

    def cli(self, *args, **kwargs):
        return subprocess.run(
            [sys.executable, "-m", "ledger", "--file", self.file, *args],
            cwd=ROOT, capture_output=True, text=True, timeout=30, **kwargs,
        )

    def add(self, date, amount, category, *extra):
        result = self.cli("add", date, amount, category, *extra)
        self.assertEqual(result.returncode, 0, result.stderr)

    def assertCleanError(self, result):
        """A user error: non-zero exit, a message on stderr, no traceback."""
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr.strip())
        self.assertNotIn("Traceback", result.stderr)

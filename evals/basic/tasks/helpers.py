"""Shared helpers for hidden acceptance tests: run the CLI as a user would."""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CliCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.file = os.path.join(self.dir.name, "b.json")

    def tearDown(self):
        self.dir.cleanup()

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "bookmarks", "--file", self.file, *args],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )

    def add(self, url, title, *tags):
        extra = [arg for tag in tags for arg in ("--tag", tag)]
        result = self.cli("add", url, title, *extra)
        self.assertEqual(result.returncode, 0, result.stderr)

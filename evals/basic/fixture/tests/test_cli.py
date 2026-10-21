import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from bookmarks.cli import main


def run(*argv):
    out = io.StringIO()
    with redirect_stdout(out):
        code = main(list(argv))
    return code, out.getvalue()


class CliTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.file = os.path.join(self.dir.name, "b.json")

    def tearDown(self):
        self.dir.cleanup()

    def test_add_then_list(self):
        run("--file", self.file, "add", "https://a.example", "Alpha", "--tag", "news")
        code, out = run("--file", self.file, "list")
        self.assertEqual(code, 0)
        self.assertEqual(out, "1  Alpha  https://a.example  #news\n")

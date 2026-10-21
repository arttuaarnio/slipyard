from tests.helpers import CliCase


class PagingTest(CliCase):
    def setUp(self):
        super().setUp()
        for n in range(1, 6):
            self.add(f"https://{n}.example", f"Item{n}")

    def ids(self, *args):
        result = self.cli("list", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return [line.split()[0] for line in result.stdout.splitlines()]

    def test_limit(self):
        self.assertEqual(self.ids("--limit", "2"), ["1", "2"])

    def test_offset(self):
        self.assertEqual(self.ids("--offset", "3"), ["4", "5"])

    def test_limit_and_offset(self):
        self.assertEqual(self.ids("--limit", "2", "--offset", "1"), ["2", "3"])

    def test_offset_past_end(self):
        self.assertEqual(self.ids("--offset", "10"), [])

    def test_invalid_values_are_usage_errors(self):
        for args in (["--limit", "0"], ["--limit", "-1"], ["--offset", "-1"], ["--limit", "x"]):
            result = self.cli("list", *args)
            self.assertEqual(result.returncode, 2, args)
            self.assertEqual(result.stdout, "", args)
            self.assertTrue(result.stderr, args)

    def test_no_flags_lists_all(self):
        self.assertEqual(self.ids(), ["1", "2", "3", "4", "5"])

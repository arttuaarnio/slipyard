from tests.helpers import CliCase


class TagFilterTest(CliCase):
    def setUp(self):
        super().setUp()
        self.add("https://a.example", "Alpha", "News", "tech")
        self.add("https://b.example", "Beta", "news")
        self.add("https://c.example", "Gamma", "tech")

    def ids(self, *args):
        result = self.cli("list", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return [line.split()[0] for line in result.stdout.splitlines()]

    def test_single_tag(self):
        self.assertEqual(self.ids("--tag", "tech"), ["1", "3"])

    def test_case_insensitive(self):
        self.assertEqual(self.ids("--tag", "NEWS"), ["1", "2"])

    def test_multiple_tags_mean_all(self):
        self.assertEqual(self.ids("--tag", "news", "--tag", "TECH"), ["1"])

    def test_no_match_prints_nothing(self):
        result = self.cli("list", "--tag", "missing")
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_format_unchanged(self):
        out = self.cli("list", "--tag", "news").stdout.splitlines()
        self.assertEqual(out[1], "2  Beta  https://b.example  #news")

    def test_without_tag_lists_all(self):
        self.assertEqual(self.ids(), ["1", "2", "3"])

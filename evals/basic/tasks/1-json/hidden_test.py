import json

from tests.helpers import CliCase


class JsonTest(CliCase):
    def test_empty_prints_empty_array(self):
        result = self.cli("list", "--json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), [])

    def test_items_with_exact_keys_in_id_order(self):
        self.add("https://a.example", "Alpha", "news")
        self.add("https://b.example", "Beta")
        data = json.loads(self.cli("list", "--json").stdout)
        self.assertEqual(data, [
            {"id": 1, "url": "https://a.example", "title": "Alpha", "tags": ["news"]},
            {"id": 2, "url": "https://b.example", "title": "Beta", "tags": []},
        ])

    def test_stdout_is_only_json(self):
        self.add("https://a.example", "Alpha")
        out = self.cli("list", "--json").stdout
        json.loads(out)  # raises if anything else is printed
        self.assertTrue(out.strip().startswith("["))

    def test_unicode_title_round_trips(self):
        self.add("https://a.example", "Café ☕")
        data = json.loads(self.cli("list", "--json").stdout)
        self.assertEqual(data[0]["title"], "Café ☕")

    def test_plain_output_unchanged(self):
        self.add("https://a.example", "Alpha", "news")
        self.assertEqual(self.cli("list").stdout, "1  Alpha  https://a.example  #news\n")

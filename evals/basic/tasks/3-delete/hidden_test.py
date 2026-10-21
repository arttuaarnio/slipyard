from tests.helpers import CliCase


class DeleteTest(CliCase):
    def titles(self):
        return [line.split("  ")[1] for line in self.cli("list").stdout.splitlines()]

    def test_deletes_the_right_item_after_gaps(self):
        for name in ("A", "B", "C", "D"):
            self.add(f"https://{name.lower()}.example", name)
        self.assertEqual(self.cli("delete", "1").returncode, 0)
        self.assertEqual(self.cli("delete", "3").returncode, 0)
        self.assertEqual(self.titles(), ["B", "D"])

    def test_missing_id_errors_and_keeps_file(self):
        self.add("https://a.example", "A")
        with open(self.file, encoding="utf-8") as f:
            before = f.read()
        result = self.cli("delete", "7")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no bookmark with id 7", result.stderr)
        with open(self.file, encoding="utf-8") as f:
            self.assertEqual(f.read(), before)

    def test_missing_id_on_empty_store(self):
        result = self.cli("delete", "1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no bookmark with id 1", result.stderr)

    def test_ids_are_never_reused(self):
        self.add("https://a.example", "A")
        self.add("https://b.example", "B")
        self.cli("delete", "2")
        self.assertEqual(self.cli("add", "https://c.example", "C").stdout.strip(), "added 3")

    def test_ids_not_reused_after_deleting_everything(self):
        self.add("https://a.example", "A")
        self.cli("delete", "1")
        self.assertEqual(self.cli("add", "https://b.example", "B").stdout.strip(), "added 2")

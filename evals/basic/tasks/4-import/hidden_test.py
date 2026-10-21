import os

from tests.helpers import CliCase


class ImportTest(CliCase):
    def csv(self, text):
        path = os.path.join(self.dir.name, "in.csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        return path

    def items(self):
        """Bookmarks as the list command shows them: id, title, url, then #tags."""
        items = []
        for line in self.cli("list").stdout.splitlines():
            parts = line.split("  ")
            tags = parts[3].split() if len(parts) > 3 else []
            items.append({"title": parts[1], "url": parts[2], "tags": [t.lstrip("#") for t in tags]})
        return items

    def test_imports_valid_rows_with_tags(self):
        path = self.csv("url,title,tags\nhttps://a.example,Alpha, news ; tech \nhttp://b.example,Beta,\n")
        result = self.cli("import", path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "imported 2, skipped 0")
        items = self.items()
        self.assertEqual([i["title"] for i in items], ["Alpha", "Beta"])
        self.assertEqual(items[0]["tags"], ["news", "tech"])
        self.assertEqual(items[1]["tags"], [])

    def test_skips_invalid_rows(self):
        path = self.csv("url,title,tags\nftp://x.example,Bad scheme,\nhttps://c.example,,\nhttps://d.example,Delta,a;;b\n")
        result = self.cli("import", path)
        self.assertEqual(result.stdout.strip(), "imported 1, skipped 2")
        self.assertEqual(self.items()[0]["tags"], ["a", "b"])

    def test_skips_duplicates_existing_and_within_file(self):
        self.add("https://a.example", "Existing")
        path = self.csv("url,title,tags\nhttps://a.example,Again,\nhttps://e.example,Echo,\nhttps://e.example,Echo again,\n")
        result = self.cli("import", path)
        self.assertEqual(result.stdout.strip(), "imported 1, skipped 2")
        self.assertEqual([i["title"] for i in self.items()], ["Existing", "Echo"])

    def test_quoted_title_with_comma(self):
        path = self.csv('url,title,tags\nhttps://f.example,"Foxtrot, the sequel",x\n')
        self.cli("import", path)
        self.assertEqual(self.items()[0]["title"], "Foxtrot, the sequel")

    def test_missing_file(self):
        result = self.cli("import", os.path.join(self.dir.name, "nope.csv"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("nope.csv", result.stderr)

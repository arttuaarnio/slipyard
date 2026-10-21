import os
import tempfile
import unittest

from bookmarks.store import Store


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.store = Store(os.path.join(self.dir.name, "b.json"))

    def tearDown(self):
        self.dir.cleanup()

    def test_empty_store_lists_nothing(self):
        self.assertEqual(self.store.list(), [])

    def test_add_assigns_increasing_ids(self):
        first = self.store.add("https://a.example", "A")
        second = self.store.add("https://b.example", "B", ["x"])
        self.assertEqual((first["id"], second["id"]), (1, 2))
        self.assertEqual(self.store.list()[1]["tags"], ["x"])

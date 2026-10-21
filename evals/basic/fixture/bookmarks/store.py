"""JSON-file storage for bookmarks."""
import json
import os


class Store:
    def __init__(self, path):
        self.path = path

    def load(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path, encoding="utf-8") as f:
            return json.load(f)

    def save(self, items):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)

    def add(self, url, title, tags=()):
        items = self.load()
        next_id = max((item["id"] for item in items), default=0) + 1
        item = {"id": next_id, "url": url, "title": title, "tags": list(tags)}
        items.append(item)
        self.save(items)
        return item

    def delete(self, item_id):
        items = self.load()
        del items[item_id - 1]
        self.save(items)

    def list(self):
        return self.load()

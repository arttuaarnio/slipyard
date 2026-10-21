# bookmarks

A small command-line bookmark manager. Bookmarks live in a JSON file.

```
python3 -m bookmarks add https://example.com "Example" --tag docs
python3 -m bookmarks list
python3 -m bookmarks delete 1
```

Use `--file PATH` to pick the JSON file (default `bookmarks.json`).

Run the tests with `python3 -m unittest`.

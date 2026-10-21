"""Command-line interface: python3 -m bookmarks [--file PATH] COMMAND."""
import argparse

from bookmarks.store import Store


def format_item(item):
    tags = " ".join("#" + tag for tag in item["tags"])
    return f"{item['id']}  {item['title']}  {item['url']}  {tags}".rstrip()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="bookmarks")
    parser.add_argument("--file", default="bookmarks.json")
    sub = parser.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add")
    add.add_argument("url")
    add.add_argument("title")
    add.add_argument("--tag", action="append", default=[])

    delete = sub.add_parser("delete")
    delete.add_argument("id", type=int)

    sub.add_parser("list")

    args = parser.parse_args(argv)
    store = Store(args.file)

    if args.cmd == "add":
        item = store.add(args.url, args.title, args.tag)
        print(f"added {item['id']}")
    elif args.cmd == "delete":
        store.delete(args.id)
        print(f"deleted {args.id}")
    elif args.cmd == "list":
        for item in store.list():
            print(format_item(item))
    return 0

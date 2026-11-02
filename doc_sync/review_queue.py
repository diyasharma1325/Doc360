"""Stage 5 support: the list of pending items you and your team work
through — approve, reject, or resolve a flagged merge conflict. Backed by
a JSON file for the MVP; a real UI can replace this later without
changing how the rest of the pipeline calls it.
"""
import argparse
import json
import os
import uuid
from datetime import datetime, timezone

import notify

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "data", "review_queue.json")


def load(path=DEFAULT_PATH):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def save(items, path=DEFAULT_PATH):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(items, f, indent=2)


def add(entry, path=DEFAULT_PATH):
    items = load(path)
    entry = dict(entry)
    entry["id"] = str(uuid.uuid4())[:8]
    entry["created_at"] = datetime.now(timezone.utc).isoformat()
    items.append(entry)
    save(items, path)
    notify.notify_new_review_item(entry)
    return entry


def list_pending(path=DEFAULT_PATH):
    return [i for i in load(path) if i["status"] in ("pending", "merge_conflict")]


def mark(item_id, status, path=DEFAULT_PATH):
    items = load(path)
    for item in items:
        if item["id"] == item_id:
            item["status"] = status
            item["resolved_at"] = datetime.now(timezone.utc).isoformat()
            save(items, path)
            return item
    raise KeyError(f"No queue item with id {item_id}")


def main():
    parser = argparse.ArgumentParser(description="Inspect and resolve the review queue.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List pending and merge-conflict items")

    approve_p = sub.add_parser("approve", help="Mark an item approved")
    approve_p.add_argument("item_id")

    reject_p = sub.add_parser("reject", help="Mark an item rejected")
    reject_p.add_argument("item_id")

    args = parser.parse_args()
    if args.command == "list":
        for item in list_pending():
            print(f"[{item['id']}] ({item['status']}) article={item['article_id']} "
                  f"feature={item['feature_area']} confidence={item['confidence']}")
            print(f"    {item['rationale']}")
            verification = item.get("verification")
            if verification and not verification["ok"]:
                for warning in verification["warnings"]:
                    print(f"    ⚠ verification: {warning}")
    elif args.command == "approve":
        mark(args.item_id, "approved")
        print(f"{args.item_id} marked approved.")
    elif args.command == "reject":
        mark(args.item_id, "rejected")
        print(f"{args.item_id} marked rejected.")


if __name__ == "__main__":
    main()

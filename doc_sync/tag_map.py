"""Stage 2 support: the feature-area -> article-id map that makes
candidate lookup a dictionary read instead of a full-KB scan. For the MVP
this is hand-seeded, not built from a real crawl — see `seed` below.
"""
import argparse
import json
import os

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "data", "tag_map.json")


def load(path=DEFAULT_PATH):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def save(data, path=DEFAULT_PATH):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def lookup(feature_area, path=DEFAULT_PATH):
    return load(path).get(feature_area, [])


def record(feature_area, article_ids, path=DEFAULT_PATH):
    data = load(path)
    existing = set(data.get(feature_area, []))
    existing.update(article_ids)
    data[feature_area] = sorted(existing)
    save(data, path)
    return data[feature_area]


def main():
    parser = argparse.ArgumentParser(description="Seed or inspect the feature-area tag map.")
    sub = parser.add_subparsers(dest="command", required=True)

    seed_p = sub.add_parser("seed", help="Add article IDs under a feature area")
    seed_p.add_argument("--feature", required=True)
    seed_p.add_argument("--articles", required=True, help="Comma-separated article IDs")

    sub.add_parser("list", help="Print the current tag map")

    args = parser.parse_args()
    if args.command == "seed":
        ids = [a.strip() for a in args.articles.split(",") if a.strip()]
        updated = record(args.feature, ids)
        print(f"{args.feature}: {updated}")
    else:
        print(json.dumps(load(), indent=2))


if __name__ == "__main__":
    main()

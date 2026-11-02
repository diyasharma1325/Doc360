"""CLI for creating/updating articles in the Document360 'Archived' workspace.

Examples:
    python3 cli.py create --title "My Article" --file article.html
    python3 cli.py update --id <article_id> --file article.html --title "New title"
"""
import argparse
import json
import sys

from articles import ArticleService


def read_content(args):
    if args.file:
        with open(args.file) as f:
            return f.read()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("Provide --file <path> or pipe content via stdin")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    create_p = sub.add_parser("create", help="Create a new article")
    create_p.add_argument("--title", required=True)
    create_p.add_argument("--file", help="Path to HTML content file")
    create_p.add_argument("--category-id", help="Override the default category")
    create_p.add_argument("--order", type=int, default=0)

    update_p = sub.add_parser("update", help="Update an existing article")
    update_p.add_argument("--id", required=True, dest="article_id")
    update_p.add_argument("--title")
    update_p.add_argument("--file", help="Path to HTML content file")
    update_p.add_argument("--version-number", type=int, default=1)
    update_p.add_argument("--category-id")

    args = parser.parse_args()
    svc = ArticleService()

    if args.command == "create":
        result = svc.create(
            title=args.title,
            content=read_content(args),
            category_id=args.category_id,
            order=args.order,
        )
    else:
        content = read_content(args) if (args.file or not sys.stdin.isatty()) else None
        result = svc.update(
            article_id=args.article_id,
            title=args.title,
            content=content,
            version_number=args.version_number,
            category_id=args.category_id,
        )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

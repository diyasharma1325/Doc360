"""A local, file-backed stand-in for Document360 — lets the whole pipeline
run and be demoed without any network call to the live API. This exists
because this session's Bash tool blocks external-system writes outright;
it is NOT a substitute for verifying the real get_article()/update()
field assumptions flagged in draft_writer.py and assess.py — that
verification still needs to happen against the live API before trusting
this on anything real.

Articles live as one JSON file per article under data/mock_archive/.
The behavior below is a modeling assumption for testing the pipeline's
logic, not a confirmed fact about how the real Document360 API behaves:

- update() on a published article flips its status back to "draft" and
  bumps version_number — simulating the "editing creates a pending draft
  layer" behavior draft_writer.py's safety check is designed around.
"""
import argparse
import json
import os
import uuid

STATUS_DRAFT = 0
STATUS_PUBLISHED = 3

STORE_DIR = os.path.join(os.path.dirname(__file__), "data", "mock_archive")


def _path(article_id):
    return os.path.join(STORE_DIR, f"{article_id}.json")


def _load(article_id):
    path = _path(article_id)
    if not os.path.exists(path):
        raise KeyError(f"No mock article with id {article_id}")
    with open(path) as f:
        return json.load(f)


def _save(record):
    os.makedirs(STORE_DIR, exist_ok=True)
    with open(_path(record["id"]), "w") as f:
        json.dump(record, f, indent=2)
    return record


class MockDocument360Client:
    """Same surface as d360_client.Document360Client that this pipeline
    actually calls — just get_article()."""

    def get_article(self, article_id, lang_code="en"):
        return {"data": _load(article_id)}


def seed_from_real(article_id, real_article):
    """Mirror a real Document360 article's current content into the local
    mock archive under the same id, so a kb_search.py-discovered real
    article can go through the existing mock-safe draft_writer path
    without the write ever touching the real API. No-op if a mock record
    for this id already exists — never overwrites in-progress mock state
    (e.g. a draft from an earlier run)."""
    if os.path.exists(_path(article_id)):
        return _load(article_id)
    record = {
        "id": article_id,
        "title": real_article.get("title", ""),
        "html_content": real_article.get("html_content", ""),
        "status": real_article.get("status", STATUS_PUBLISHED),
        "version_number": real_article.get("version_number", 1),
        "category_id": real_article.get("category_id", "mirrored-from-real"),
    }
    return _save(record)


class MockArticleService:
    """Same surface as articles.ArticleService that this pipeline calls —
    create(), update(), publish()."""

    def create(self, title, content, category_id=None, order=0, publish=False,
               publish_message="Initial publish"):
        article_id = uuid.uuid4().hex[:12]
        record = {
            "id": article_id,
            "title": title,
            "html_content": content,
            "status": STATUS_PUBLISHED if publish else STATUS_DRAFT,
            "version_number": 1,
            "category_id": category_id or "mock-archived-category",
        }
        _save(record)
        return {"data": {"id": article_id}}

    def update(self, article_id, title=None, content=None, lang_code="en",
               version_number=1, category_id=None):
        record = _load(article_id)
        if title is not None:
            record["title"] = title
        if content is not None:
            record["html_content"] = content
        if category_id is not None:
            record["category_id"] = category_id
        record["version_number"] = record.get("version_number", 1) + 1
        record["status"] = STATUS_DRAFT  # editing a published article creates a pending draft layer
        _save(record)
        return {"data": record}

    def publish(self, article_id, version_number, message="Publishing via API"):
        record = _load(article_id)
        record["status"] = STATUS_PUBLISHED
        _save(record)
        return {"data": record}


def main():
    parser = argparse.ArgumentParser(description="Inspect or seed the local mock archive.")
    sub = parser.add_subparsers(dest="command", required=True)

    create_p = sub.add_parser("create", help="Create a mock article")
    create_p.add_argument("--title", required=True)
    create_p.add_argument("--file", required=True, help="Path to HTML content file")
    create_p.add_argument("--publish", action="store_true")

    sub.add_parser("list", help="List mock articles")

    show_p = sub.add_parser("show", help="Show one mock article")
    show_p.add_argument("article_id")

    args = parser.parse_args()
    if args.command == "create":
        with open(args.file) as f:
            content = f.read()
        svc = MockArticleService()
        result = svc.create(title=args.title, content=content, publish=args.publish)
        print(json.dumps(result, indent=2))
    elif args.command == "list":
        if not os.path.isdir(STORE_DIR):
            print("(empty)")
            return
        for name in sorted(os.listdir(STORE_DIR)):
            if name.endswith(".json"):
                record = _load(name[:-5])
                print(f"{record['id']}  status={record['status']}  v{record['version_number']}  {record['title']}")
    elif args.command == "show":
        print(json.dumps(_load(args.article_id), indent=2))


if __name__ == "__main__":
    main()

"""Stage 2 (discovery), local full-text index: every published article in
the six live Document360 workspaces (core/workspaces.py), searchable by its
BODY text, not just its title, at zero model cost.

Why it exists: kb_search.py's triage hands the model every title in one
workspace in a single call (~40k prompt tokens for DAP for Web alone). So
it can only find an article whose TITLE names the feature, and widening it
to all six workspaces would grow that prompt six-fold. Searching bodies
locally and handing triage a short list fixes both at once: recall goes up
(a procedure that mentions the changed setting in step 6 is now findable)
and the prompt goes down.

    python3 doc_sync/kb_index.py build     # ~40 min, read-only
    python3 doc_sync/kb_index.py status
    python3 doc_sync/kb_index.py search "smart tip display rules" [--workspace "DAP for Web"]

Three rules, all deliberate:

- ALL OR NOTHING. A build writes a fresh database beside the live one and
  swaps it in only once every article read has succeeded. An article that
  still fails after its retries aborts the build and the existing index is
  left exactly as it was. Skipping it instead would ship an index silently
  missing articles under a fresh timestamp — and an article missing from
  the index is one discovery can never flag. The cost: one article that
  fails on every attempt blocks every rebuild until someone looks. Nothing
  shrinks in the meantime; the index just ages, visibly, in `status`.
- ALWAYS ALL SIX WORKSPACES. The swap replaces the whole file, so a
  one-workspace build would quietly replace a six-workspace index with a
  one-workspace one. build()'s `workspace_ids` exists for tests only and
  is refused against the default path.
- PUBLISHED ARTICLES ONLY, picked off the category tree's `public_version`
  (> 0). The tree's `status` is NOT used: it was stale on ~200 DAP for Web
  articles when checked live (2026-11-04). The body indexed is whatever
  get_article() returns, which is the LATEST version — for an article with
  a pending draft, the draft's text. Fine for discovery: draft_writer.py
  flags any such article for a manual merge regardless.

Read-only end to end. Writes only the local database:
doc_sync/data/knowledge.db (git-ignored), or $KB_INDEX_PATH.
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR.parent / "core"))  # d360_client.py / workspaces.py live in ../core

import requests
from bs4 import BeautifulSoup

import workspaces
from d360_client import Document360Client

DEFAULT_DB_PATH = os.environ.get("KB_INDEX_PATH") or str(THIS_DIR / "data" / "knowledge.db")

REQUEST_GAP_S = 0.35  # between article reads, to stay under Document360's rate limit
# Per article read. Rate limits (429) and network failures back off
# exponentially (2+4+8+16+32s, about a minute in all), because both are
# transient and a ~30-minute build should outlast a brief network drop: a
# 5-second budget lost a build ~2,100 articles in to a momentary DNS
# failure (2026-11-04). Anything else retries after 1s.
MAX_ATTEMPTS = 6

_SCHEMA = """
CREATE VIRTUAL TABLE articles USING fts5(
    title,
    category_path,
    body,
    article_id UNINDEXED,
    version_id UNINDEXED,
    workspace UNINDEXED,
    url UNINDEXED,
    tokenize = 'porter unicode61'
);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

# bm25 column weights, in schema order: a match in the title says far more
# about what an article is ABOUT than one buried in its body.
_BM25_WEIGHTS = "5.0, 2.0, 1.0"

# Document360 templating left in the HTML: a glossary term or variable
# keeps its readable name ("{{glossary.Smart Tip}}" -> "Smart Tip"), since
# that's text a reader actually sees; a snippet reference carries no text
# of its own and is dropped.
_TERM_RE = re.compile(r"\{\{(?:glossary|variable)\.([^}]+)\}\}")
_SNIPPET_RE = re.compile(r"\{\{snippet\.[^}]+\}\}")

_STOPWORDS = {
    "the", "and", "for", "with", "you", "your", "are", "this", "that", "from",
    "can", "use", "using", "how", "what", "when", "where", "which", "into", "out",
    "all", "any", "have", "has", "will", "they", "their", "them", "its", "now",
    "not", "new", "old", "also", "only", "then", "than", "more", "such",
}
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_MAX_QUERY_TERMS = 48
# search(focus=...): how much more a match on the feature's own name
# counts than a match on the rest of the change note's wording. 2 was
# picked by comparing shortlists for the saved change notes (2026-11-06).
FOCUS_WEIGHT = 2.0


class IndexBuildIncomplete(RuntimeError):
    """An article could not be read, so this build must not replace the index."""


# --- building ---------------------------------------------------------------

def _text_of(html_content):
    text = BeautifulSoup(html_content or "", "html.parser").get_text("\n")
    text = _TERM_RE.sub(r"\1", text)
    text = _SNIPPET_RE.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _published_articles(client, version_id):
    """[(category_path, article node)] for every article in a workspace's
    category tree that has a published version."""
    tree = client.list_categories(
        version_id,
        params={"excludeArticles": "false", "includeCategoryDescription": "false"},
    )
    found = []

    def walk(categories, path):
        for cat in categories or []:
            cat_path = path + [cat.get("name") or "(untitled category)"]
            for art in cat.get("articles") or []:
                if (art.get("public_version") or 0) > 0 and art.get("id"):
                    found.append((" > ".join(cat_path), art))
            walk(cat.get("child_categories"), cat_path)

    walk(tree.get("data"), [])
    return found


def _fetch_article(client, article_id):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return client.get_article(article_id)["data"]
        except Exception as exc:  # any failed read must stop the build, but only after retrying
            if attempt == MAX_ATTEMPTS:
                raise IndexBuildIncomplete(
                    f"could not read article {article_id} after {MAX_ATTEMPTS} attempts: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            transient = "429" in str(exc) or isinstance(exc, requests.exceptions.ConnectionError)
            time.sleep(2 ** attempt if transient else 1)


def build(db_path=DEFAULT_DB_PATH, client=None, workspace_ids=None):
    """Crawl every published article in the live workspaces and swap a
    fresh index in at `db_path`. Returns the number of articles indexed.
    Raises (IndexBuildIncomplete, or a Document360 error on a category
    tree) without touching an existing index when any read fails.

    `workspace_ids` narrows the crawl for TESTS ONLY, and is refused
    against the default path — see the module docstring."""
    if workspace_ids is not None and os.path.abspath(db_path) == os.path.abspath(DEFAULT_DB_PATH):
        raise ValueError("A partial build may not replace the default index; pass a different db_path.")
    ids = list(workspace_ids) if workspace_ids is not None else list(workspaces.LIVE_WORKSPACES)
    for version_id in ids:
        workspaces.require_live(version_id, "index")

    client = client or Document360Client()
    rows, per_workspace = [], {}
    for version_id in ids:
        name = workspaces.LIVE_WORKSPACES[version_id]
        pending = _published_articles(client, version_id)
        print(f"  {name}: {len(pending)} published article(s) to read...", flush=True)
        for n, (cat_path, node) in enumerate(pending, 1):
            data = _fetch_article(client, node["id"])
            body = _text_of(data.get("html_content") or "")
            if body:
                rows.append((
                    data.get("title") or node.get("title") or "",
                    cat_path,
                    body,
                    node["id"],
                    version_id,
                    name,
                    data.get("url") or node.get("url") or "",
                ))
            if n % 100 == 0:
                print(f"    {n}/{len(pending)}", flush=True)
            time.sleep(REQUEST_GAP_S)
        per_workspace[name] = sum(1 for r in rows if r[4] == version_id)

    tmp_path = db_path + ".building"
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    try:
        conn = sqlite3.connect(tmp_path)
        try:
            conn.executescript(_SCHEMA)
            conn.executemany("INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
            conn.executemany("INSERT INTO meta VALUES (?, ?)", [
                ("built_at", datetime.now(timezone.utc).isoformat(timespec="seconds")),
                ("articles", str(len(rows))),
                ("per_workspace", json.dumps(per_workspace)),
            ])
            conn.commit()
        finally:
            conn.close()
        os.replace(tmp_path, db_path)  # atomic: readers see the old index or the new one, never half of either
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    return len(rows)


# --- reading ----------------------------------------------------------------

def status(db_path=DEFAULT_DB_PATH):
    """{exists, built_at, age_hours, articles, per_workspace}. Never raises."""
    if not os.path.exists(db_path):
        return {"exists": False}
    try:
        conn = sqlite3.connect(db_path)
        try:
            meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
        finally:
            conn.close()
        built_at = datetime.fromisoformat(meta["built_at"])
        return {
            "exists": True,
            "built_at": meta["built_at"],
            "age_hours": round((datetime.now(timezone.utc) - built_at).total_seconds() / 3600, 1),
            "articles": int(meta["articles"]),
            "per_workspace": json.loads(meta.get("per_workspace", "{}")),
        }
    except (sqlite3.Error, KeyError, ValueError) as exc:
        return {"exists": True, "error": f"{type(exc).__name__}: {exc}"}


def _match_query(text):
    """Free text -> an FTS5 OR query of quoted, de-duplicated terms. Quoting
    keeps FTS5's own operator words (AND, NOT, NEAR) from being parsed as
    syntax when they appear in a change note."""
    terms = []
    for tok in _TOKEN_RE.findall((text or "").lower()):
        if len(tok) >= 3 and tok not in _STOPWORDS and tok not in terms:
            terms.append(tok)
    return " OR ".join(f'"{t}"' for t in terms[:_MAX_QUERY_TERMS])


def _focus_query(phrases):
    """Feature names ("Smart Tips", "Flows") -> an FTS5 OR query of quoted
    phrases, so "smart tips" must appear as those two words together."""
    out = []
    for phrase in phrases or []:
        words = " ".join(_TOKEN_RE.findall((phrase or "").lower()))
        if words and words not in out:
            out.append(words)
    return " OR ".join(f'"{p}"' for p in out)


def search(query, k=40, workspace=None, db_path=DEFAULT_DB_PATH, focus=None):
    """Up to `k` articles most relevant to `query`, best first (BM25,
    titles weighted above bodies), optionally narrowed to one live
    workspace by name. Each result: {article_id, title, category_path,
    workspace, version_id, url, snippet, score}, where `snippet` is the
    matching passage with hits in [brackets]. Raises FileNotFoundError if
    the index hasn't been built — callers decide whether to fall back.

    `focus` is a list of feature names. When given, only articles that
    mention at least one of them are returned, and how strongly an article
    matches them counts FOCUS_WEIGHT times as much as its match on the
    rest of `query`. Without it, a change note's everyday words ("display",
    "text", "dashboard", in a third of all articles each) decide the
    ranking, and articles that never mention the feature fill the list."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"No knowledge index at {db_path}; run: python3 doc_sync/kb_index.py build")
    match = _match_query(query)
    focus_match = _focus_query(focus)
    if not match:
        return []
    if focus_match:
        sql = (
            "WITH focus AS (SELECT rowid AS rid, "
            f"bm25(articles, {_BM25_WEIGHTS}) AS focus_score FROM articles WHERE articles MATCH ?) "
            "SELECT article_id, title, category_path, workspace, version_id, url, "
            "snippet(articles, 2, '[', ']', '…', 16) AS snippet, "
            f"bm25(articles, {_BM25_WEIGHTS}) + ? * focus.focus_score AS score "
            "FROM articles JOIN focus ON articles.rowid = focus.rid WHERE articles MATCH ?"
        )
        params = [focus_match, FOCUS_WEIGHT, match]
    else:
        sql = (
            "SELECT article_id, title, category_path, workspace, version_id, url, "
            "snippet(articles, 2, '[', ']', '…', 16) AS snippet, "
            f"bm25(articles, {_BM25_WEIGHTS}) AS score "
            "FROM articles WHERE articles MATCH ?"
        )
        params = [match]
    if workspace:
        sql += " AND workspace = ?"
        params.append(workspace)
    sql += " ORDER BY score LIMIT ?"
    params.append(k)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Build, inspect or search the local knowledge index.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help=f"Index path (default: {DEFAULT_DB_PATH})")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="Crawl all six live workspaces (read-only, ~40 min) and replace the index")
    sub.add_parser("status", help="When the index was built and what it holds")
    search_p = sub.add_parser("search", help="Search the index")
    search_p.add_argument("query")
    search_p.add_argument("--k", type=int, default=20)
    search_p.add_argument("--workspace", default=None, help=f"One of: {', '.join(workspaces.names())}")
    args = parser.parse_args()

    if args.command == "build":
        print("Building the knowledge index from all six live workspaces (read-only)...", flush=True)
        t0 = time.time()
        try:
            n = build(db_path=args.db)
        except Exception as exc:  # any failed read must leave the existing index alone
            print(f"[ERROR] build aborted, knowledge index left unchanged: {type(exc).__name__}: {exc}")
            raise SystemExit(1)
        print(f"Indexed {n} article(s) in {(time.time() - t0) / 60:.1f} min -> {args.db}")
    elif args.command == "status":
        print(json.dumps(status(args.db), indent=2))
    else:
        for r in search(args.query, k=args.k, workspace=args.workspace, db_path=args.db):
            print(f"[{r['article_id']}] {r['title']}  ({r['workspace']} > {r['category_path']})")
            print(f"    {r['snippet']}")


if __name__ == "__main__":
    main()

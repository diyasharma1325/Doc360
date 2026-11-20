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

    python3 doc_sync/kb_index.py build     # ~40 min, read-only (longer the first time with OCR)
    python3 doc_sync/kb_index.py build --no-ocr
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

SCREENSHOT TEXT (2026-11-20): a build also records every article's images
(table `images`: position, path, alt text, step text) and, when Tesseract
is installed, the text inside them, in the `screens` column ("Screenshot
3: ..."), so discovery can find an article whose TEXT is already right but
whose screenshots still show the old UI. OCR results are kept per image in
data/screenshots.db (screenshots.py), so only images new since the last
build are read; the first build with OCR takes much longer. An index built
before this has neither; discovery works without them.

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
OCR_WORKERS = 6    # articles OCR'd at once during a build (each with 2 download/OCR threads)
OCR_BACKLOG = 40   # articles queued for OCR before the crawl waits

_SCHEMA = """
CREATE VIRTUAL TABLE articles USING fts5(
    title,
    category_path,
    body,
    article_id UNINDEXED,
    version_id UNINDEXED,
    workspace UNINDEXED,
    url UNINDEXED,
    screens,
    tokenize = 'porter unicode61'
);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE images (
    article_id TEXT NOT NULL, n INTEGER NOT NULL, path TEXT NOT NULL, alt TEXT, step_text TEXT,
    PRIMARY KEY (article_id, n)
);
CREATE INDEX images_path ON images (path);
"""

# bm25 column weights, in schema order: a match in the title says far more
# about what an article is ABOUT than one buried in its body. Columns past
# the third (the unindexed ones, and `screens`) take FTS5's default of 1.0,
# so screenshot text counts as much as body text.
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
# Content type names writers spell as one word but articles hyphenate. The
# tokenizer splits "Pop-ups" into "pop ups", so "Popups" alone matched 115
# articles against 647 for "pop ups" (2026-11-06).
_FOCUS_ALIASES = {"popups": "pop ups", "popup": "pop up"}


# What an article's indexed body is made of, recorded in the index's meta
# so `status` shows whether an index predates a change to it.
BODY_INCLUDES = "text, image alt text"
SCREENS_INCLUDES = "screenshot text (OCR)"


class IndexBuildIncomplete(RuntimeError):
    """An article could not be read, so this build must not replace the index."""


# --- building ---------------------------------------------------------------

# Alt text that says nothing about the image: a bare file name, a generic
# word, or an id. Kept out so it doesn't add noise to every article.
_GENERIC_ALT = {"image", "img", "screenshot", "screen shot", "picture", "pic", "photo", "gif", "png",
                "jpg", "jpeg", "icon", "logo", "untitled", "blank"}
_ALT_EXT_RE = re.compile(r"\.(png|jpe?g|gif|svg|webp|bmp)$", re.IGNORECASE)


def _alt_text(alt):
    """An image's alt text as indexable words, or "" when it carries none.
    "Click_launchers.png" -> "Click launchers"."""
    text = _ALT_EXT_RE.sub("", (alt or "").strip())
    text = re.sub(r"[_\-]+", " ", text)
    text = " ".join(text.split())
    words = re.findall(r"[A-Za-z]{2,}", text)
    if not words or text.lower() in _GENERIC_ALT or re.fullmatch(r"[0-9a-fA-F ]{8,}", text):
        return ""
    if len(words) == 1 and re.fullmatch(r"(image|img|screenshot)\s*\d*", text.lower()):
        return ""
    return text


def _text_of(html_content):
    """An article's indexable text: its visible text, plus each image's alt
    text where the image sits (2026-11-09). Screenshots carry much of an
    article's context ("Customize a Launcher": 11 images, 335 words, and
    "Dashboard" only in its screenshots), and the alt text is the part of
    that we can read for free. Text inside the images (OCR) is not read."""
    soup = BeautifulSoup(html_content or "", "html.parser")
    for img in soup.find_all("img"):
        alt = _alt_text(img.get("alt"))
        img.replace_with(f"\n{alt}\n" if alt else "")
    text = soup.get_text("\n")
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


def build(db_path=DEFAULT_DB_PATH, client=None, workspace_ids=None, read_screens=True):
    """Crawl every published article in the live workspaces and swap a
    fresh index in at `db_path`. Returns the number of articles indexed.
    Raises (IndexBuildIncomplete, or a Document360 error on a category
    tree) without touching an existing index when any read fails.

    `workspace_ids` narrows the crawl for TESTS ONLY, and is refused
    against the default path — see the module docstring. `read_screens`
    False skips OCR (images are still recorded, and screenshot text
    already in data/screenshots.db is still used)."""
    import screenshots

    if workspace_ids is not None and os.path.abspath(db_path) == os.path.abspath(DEFAULT_DB_PATH):
        raise ValueError("A partial build may not replace the default index; pass a different db_path.")
    ids = list(workspace_ids) if workspace_ids is not None else list(workspaces.LIVE_WORKSPACES)
    for version_id in ids:
        workspaces.require_live(version_id, "index")

    client = client or Document360Client()
    ocr_on = read_screens and screenshots.tesseract_available()
    if read_screens and not ocr_on:
        print("  (Tesseract isn't installed: images are recorded, but the text in them isn't read)")
    rows, image_rows, per_workspace = [], [], {}
    # OCR runs beside the crawl, across articles, in OCR_WORKERS threads. The
    # crawl waits while more than OCR_BACKLOG articles are queued: an image's
    # signed URL expires ~15 minutes after the read, so OCR must keep up.
    # One article at a time read about one image a second (2026-11-20).
    from concurrent.futures import ThreadPoolExecutor
    import threading
    pool = ThreadPoolExecutor(max_workers=OCR_WORKERS) if ocr_on else None
    backlog = threading.BoundedSemaphore(OCR_BACKLOG)
    screens_of = {}  # row index -> future or text

    def ocr_job(images):
        try:
            return screenshots.screens_text(images, screenshots.ocr_images(images, workers=2))
        finally:
            backlog.release()

    for version_id in ids:
        name = workspaces.LIVE_WORKSPACES[version_id]
        pending = _published_articles(client, version_id)
        print(f"  {name}: {len(pending)} published article(s) to read...", flush=True)
        for n, (cat_path, node) in enumerate(pending, 1):
            data = _fetch_article(client, node["id"])
            html_content = data.get("html_content") or ""
            body = _text_of(html_content)
            images = screenshots.article_images(html_content)
            screens = ""
            if images and body:
                if pool:
                    backlog.acquire()
                    screens_of[len(rows)] = pool.submit(ocr_job, images)
                else:
                    screens = screenshots.screens_text(images, screenshots.cached_ocr([i["path"] for i in images]))
            if body:
                image_rows += [(node["id"], i["n"], i["path"], i["alt"], i["step_text"]) for i in images]
                rows.append((
                    data.get("title") or node.get("title") or "",
                    cat_path,
                    body,
                    node["id"],
                    version_id,
                    name,
                    data.get("url") or node.get("url") or "",
                    screens,
                ))
            if n % 100 == 0:
                print(f"    {n}/{len(pending)}", flush=True)
            time.sleep(REQUEST_GAP_S)
        per_workspace[name] = sum(1 for r in rows if r[4] == version_id)
    if pool:
        pool.shutdown(wait=True)
        for k, fut in screens_of.items():
            try:
                text = fut.result()
            except Exception as exc:  # OCR only helps discovery: never fail the build over it
                print(f"    (OCR failed for {rows[k][3]}: {type(exc).__name__}: {exc})")
                text = ""
            rows[k] = rows[k][:7] + (text,)

    tmp_path = db_path + ".building"
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    try:
        conn = sqlite3.connect(tmp_path)
        try:
            conn.executescript(_SCHEMA)
            conn.executemany("INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
            # OR IGNORE: an article filed in two categories is read twice, with the same images
            conn.executemany("INSERT OR IGNORE INTO images VALUES (?, ?, ?, ?, ?)", image_rows)
            built_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            conn.executemany("INSERT INTO meta VALUES (?, ?)", [
                ("built_at", built_at),
                ("screens_updated_at", built_at),
                ("articles", str(len(rows))),
                ("per_workspace", json.dumps(per_workspace)),
                ("body_includes", BODY_INCLUDES),
                ("screens_includes", SCREENS_INCLUDES if ocr_on else "images recorded, text not read"),
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
            # An index built before alt text was read has no such key.
            "body_includes": meta.get("body_includes", "text"),
            # Nor one built before screenshots were recorded (2026-11-20).
            "screens_includes": meta.get("screens_includes", "none"),
            "screens_updated_at": meta.get("screens_updated_at", meta["built_at"]),
        }
    except (sqlite3.Error, KeyError, ValueError) as exc:
        return {"exists": True, "error": f"{type(exc).__name__}: {exc}"}


def has_screens(db_path=DEFAULT_DB_PATH):
    """True when the index records images and screenshot text (built after
    2026-11-20)."""
    if not os.path.exists(db_path):
        return False
    conn = sqlite3.connect(db_path)
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(articles)")]
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        return "screens" in cols and "images" in tables
    finally:
        conn.close()


def article_ids(workspace=None, db_path=DEFAULT_DB_PATH):
    """Every indexed article id, in one workspace (by name) or all."""
    where, extra = _workspace_filter(workspace)
    conn = sqlite3.connect(db_path)
    try:
        return [r[0] for r in conn.execute("SELECT article_id FROM articles WHERE 1 = 1" + where, extra)]
    finally:
        conn.close()


def images_of(article_id, db_path=DEFAULT_DB_PATH):
    """[{n, path, alt, step_text}] recorded for one article (empty for an
    index without screenshots)."""
    if not has_screens(db_path):
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(
            "SELECT n, path, alt, step_text FROM images WHERE article_id = ? ORDER BY n", (article_id,))]
    finally:
        conn.close()


def where_image(path, db_path=DEFAULT_DB_PATH):
    """[{article_id, n, title, workspace}] for every indexed article that
    shows the image at `path`."""
    if not has_screens(db_path):
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(
            "SELECT i.article_id, i.n, a.title, a.workspace FROM images i JOIN articles a "
            "ON a.article_id = i.article_id WHERE i.path = ?", (path,))]
    finally:
        conn.close()


def update_screens(updates, db_path=DEFAULT_DB_PATH):
    """Write screenshot text and image lists into the index in place:
    {article_id: (images, screens_text)}. Used by `screenshots.py ocr` to
    fill one workspace without a rebuild. Refused on an index built before
    screenshots were recorded. Returns the number of articles updated."""
    if not has_screens(db_path):
        raise SystemExit("This knowledge index was built before screenshots were recorded. Rebuild it "
                         "first: python3 doc_sync/kb_index.py build")
    conn = sqlite3.connect(db_path)
    try:
        n = 0
        for aid, (images, screens) in updates.items():
            cur = conn.execute("UPDATE articles SET screens = ? WHERE article_id = ?", (screens, aid))
            if cur.rowcount:
                n += 1
                conn.execute("DELETE FROM images WHERE article_id = ?", (aid,))
                conn.executemany("INSERT INTO images VALUES (?, ?, ?, ?, ?)",
                                 [(aid, i["n"], i["path"], i["alt"], i["step_text"]) for i in images])
        conn.execute("INSERT OR REPLACE INTO meta VALUES ('screens_updated_at', ?)",  # microseconds: an
                     (datetime.now(timezone.utc).isoformat(timespec="microseconds"),))  # update in the build's second still counts
        conn.execute("INSERT OR REPLACE INTO meta VALUES ('screens_includes', ?)", (SCREENS_INCLUDES,))
        conn.commit()
        return n
    finally:
        conn.close()


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
        for variant in (words, _FOCUS_ALIASES.get(words)):
            if variant and variant not in out:
                out.append(variant)
    return " OR ".join(f'"{p}"' for p in out)


def _workspace_filter(workspace):
    """SQL and params narrowing a query to one workspace name or a list of
    them; ("", []) for None or an empty list (every workspace)."""
    if not workspace:
        return "", []
    names = [workspace] if isinstance(workspace, str) else list(workspace)
    return f" AND workspace IN ({', '.join('?' * len(names))})", names


def phrase_count(phrase, workspace=None, db_path=DEFAULT_DB_PATH):
    """How many indexed articles contain `phrase` as consecutive words.
    `workspace` is one name, a list of names, or None for all."""
    match = _focus_query([phrase])
    if not match:
        return 0
    where, extra = _workspace_filter(workspace)
    sql, params = "SELECT count(*) FROM articles WHERE articles MATCH ?" + where, [match] + extra
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql, params).fetchone()[0]
    finally:
        conn.close()


def search(query, k=40, workspace=None, db_path=DEFAULT_DB_PATH, focus=None):
    """Up to `k` articles most relevant to `query`, best first (BM25,
    titles weighted above bodies), optionally narrowed to one live
    workspace by name, or to a list of them. Each result: {article_id, title, category_path,
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
    where, extra = _workspace_filter(workspace)
    sql += where
    params.extend(extra)
    sql += " ORDER BY score LIMIT ?"
    params.append(k)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def about(names, query, workspace=None, k=200, db_path=DEFAULT_DB_PATH):
    """Every article whose TITLE or CATEGORY names one of `names` (content
    types such as "Launchers"), up to `k`, ranked by how well its text
    matches `query`. Same result shape as search(); `snippet` shows the
    passage that best matches `query`. This is the content-type sweep
    (kb_search.py): an article titled "Customize a Launcher" or filed under
    "In-app Content > Launcher" is about Launchers whatever else it says,
    so it must not depend on ranking well against a change note's wording."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"No knowledge index at {db_path}; run: python3 doc_sync/kb_index.py build")
    names_match = _focus_query(names)
    if not names_match:
        return []
    query_match = _match_query(query)
    # Every swept article matches the OR (its title or category holds one of
    # the names), so the second clause only ranks, never filters.
    expr = f"{{title category_path}} : ({names_match})"
    expr += f" AND ({query_match} OR {names_match})" if query_match else ""
    sql = (
        "SELECT article_id, title, category_path, workspace, version_id, url, "
        "snippet(articles, 2, '[', ']', '…', 16) AS snippet, "
        f"bm25(articles, {_BM25_WEIGHTS}) AS score FROM articles WHERE articles MATCH ?"
    )
    params = [expr]
    where, extra = _workspace_filter(workspace)
    sql += where + " ORDER BY score LIMIT ?"
    params += extra + [k]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def count_about(names, workspace=None, db_path=DEFAULT_DB_PATH):
    """How many articles about() would return with no limit."""
    names_match = _focus_query(names)
    if not names_match:
        return 0
    where, extra = _workspace_filter(workspace)
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT count(*) FROM articles WHERE articles MATCH ?" + where,
                            [f"{{title category_path}} : ({names_match})"] + extra).fetchone()[0]
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Build, inspect or search the local knowledge index.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help=f"Index path (default: {DEFAULT_DB_PATH})")
    sub = parser.add_subparsers(dest="command", required=True)
    build_p = sub.add_parser("build", help="Crawl all six live workspaces (read-only, ~40 min) and replace the index")
    build_p.add_argument("--no-ocr", action="store_true",
                         help="Don't read the text in images new since the last build")
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
            n = build(db_path=args.db, read_screens=not args.no_ocr)
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

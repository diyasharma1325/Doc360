"""Phase 2, archive articles: an approved article marked "archive" (by
agent discovery: the change removes its main subject) is NOT edited.
Instead phase 2 works out a recommendation for the writer:

- a REDIRECT TARGET for its URL, with a reason and a runner-up;
- the articles that LINK TO or mention it: the approved ones get an edit
  that repoints the link (ticket_run.py passes repoint_instruction() to
  assessment), the rest are listed for the writer to update by hand, and
  release notes are left as they are;
- DEPENDENT articles that only make sense alongside it (consider archiving
  them too), and links from it that don't resolve to any published
  article (often an unpublished FAQ about the same feature).

The recommendation goes in the phase 2 comment ONLY (writer decision,
2026-11-11). Nothing is archived and no redirect is set up: the writer
does both in Document360.

How the target is chosen: candidates are gathered without a model call
(the article's category siblings in the plain-text copy, the articles its
live HTML links to, and the articles that mention its title), then ONE
`claude -p` call, no tools, picks the target, the runner-up and the
dependents (prompts/archive.md). Ids it returns outside the candidate list
are dropped.

Read-only: the live article (Document360, read), the local index and the
copy (kb_mirror.py).
"""
import re
import sqlite3
from pathlib import Path

import claude_call
import kb_index
import kb_mirror
import kb_search

THIS_DIR = Path(__file__).resolve().parent
PROMPT_PATH = THIS_DIR / "prompts" / "archive.md"
MODEL = claude_call.DEFAULT_MODEL

ARCHIVED_TEXT_MAX = 6000   # chars of the archived article shown to the model
EXCERPT_MAX = 450          # chars of each candidate's opening text
SIBLINGS_MAX = 30
MENTIONS_MAX = 25

_HREF_RE = re.compile(r'<a\b[^>]*\bhref="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
_TAG_RE = re.compile(r"<[^>]+>")

SCHEMA = {
    "type": "object",
    "properties": {
        "redirect_to": {"type": "string", "description": "A candidate id, or empty for no sensible target"},
        "reason": {"type": "string"},
        "runner_up": {"type": "string", "description": "A candidate id, or empty"},
        "dependents": {
            "type": "array",
            "items": {"type": "object",
                      "properties": {"article_id": {"type": "string"}, "reason": {"type": "string"}},
                      "required": ["article_id", "reason"]},
        },
    },
    "required": ["redirect_to", "reason", "runner_up", "dependents"],
}


def _slug(url_or_href):
    return (url_or_href or "").split("?")[0].split("#")[0].rstrip("/").rsplit("/", 1)[-1].lower()


def _rows(workspace, db_path=kb_index.DEFAULT_DB_PATH):
    """{article_id: {title, category_path, url, workspace}} for one workspace."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT article_id, title, category_path, url FROM articles WHERE workspace = ?",
                            (workspace,)).fetchall()
    finally:
        conn.close()
    return {r[0]: {"article_id": r[0], "title": r[1], "category_path": r[2], "url": r[3], "workspace": workspace}
            for r in rows}


def _body(article_id, manifest):
    rel = manifest.get(article_id)
    if not rel:
        return ""
    text = (kb_mirror.DEFAULT_MIRROR_PATH / rel).read_text(encoding="utf-8")
    return text.split("\n---\n", 1)[-1].strip()


def links_in(html_content):
    """[(href, link text)] in an article's HTML, mailto/anchors left out."""
    out = []
    for href, text in _HREF_RE.findall(html_content or ""):
        href = href.replace("&amp;", "&")
        if href.startswith(("mailto:", "#", "javascript:")):
            continue
        out.append((href, " ".join(_TAG_RE.sub("", text).split())))
    return out


def is_release_note(row):
    return "release note" in (row.get("category_path") or "").lower() or \
        re.search(r"\brelease\b", row.get("title") or "", re.I) is not None


def links_to(html_content, archived):
    """True if `html_content` has a link to the archived article's URL."""
    target = _slug(archived["url"])
    return any(_slug(h) == target for h, _ in links_in(html_content))


def mentions(text, archived):
    return archived["title"].lower() in (text or "").lower()


def gather(archived_id, live_html, workspace, skip_ids=(), db_path=kb_index.DEFAULT_DB_PATH):
    """The candidates and link facts for one archived article, no model call:
    {archived, siblings, outbound, unresolved, mentioned_by}. `skip_ids`
    (other articles being archived) are never candidates."""
    kb_mirror.ensure_fresh(db_path=db_path)
    manifest = kb_mirror.manifest()
    rows = _rows(workspace, db_path)
    archived = rows.get(archived_id) or {"article_id": archived_id, "title": "", "category_path": "",
                                         "url": "", "workspace": workspace}
    skip = set(skip_ids) | {archived_id}
    by_slug = {_slug(r["url"]): r for r in rows.values()}

    siblings = [r for r in rows.values()
                if r["category_path"] == archived["category_path"] and r["article_id"] not in skip][:SIBLINGS_MAX]

    outbound, unresolved, seen = [], [], set()
    for href, text in links_in(live_html):
        r = by_slug.get(_slug(href))
        if r and r["article_id"] not in skip and r["article_id"] not in seen:
            seen.add(r["article_id"])
            outbound.append(r)
        elif not r and ("/docs/" in href or href.startswith("/")):
            unresolved.append({"text": text, "href": href})

    mentioned_by = []
    if archived["title"]:
        for aid, r in rows.items():
            if aid in skip:
                continue
            if mentions(_body(aid, manifest), archived):
                mentioned_by.append(r)
            if len(mentioned_by) >= MENTIONS_MAX:
                break
    return {"archived": archived, "siblings": siblings, "outbound": outbound, "unresolved": unresolved,
            "mentioned_by": mentioned_by}


def _candidate_block(r, manifest, tag):
    excerpt = " ".join(_body(r["article_id"], manifest)[:EXCERPT_MAX].split())
    return f"- [{r['article_id']}] {r['title']} ({r['category_path']})  [{tag}]\n    {excerpt}"


def choose(change_note, facts, model=MODEL):
    """One model call -> {redirect, runner_up, reason, dependents}; each
    article a row dict (or None). Ids outside the candidates are dropped."""
    manifest = kb_mirror.manifest()
    tags = {}
    for key, tag in (("siblings", "same category"), ("outbound", "it links here"),
                     ("mentioned_by", "mentions it")):
        for r in facts[key]:
            tags.setdefault(r["article_id"], (r, []))[1].append(tag)
    if not tags:
        return {"redirect": None, "runner_up": None, "reason": "No candidate articles were found.", "dependents": []}

    a = facts["archived"]
    lines = kb_search.note_block(change_note) + [
        "", f"Article being archived: {a['title']} ({a['category_path']})",
        _body(a["article_id"], manifest)[:ARCHIVED_TEXT_MAX], "",
        f"Candidates ({len(tags)}):",
    ] + [_candidate_block(r, manifest, ", ".join(t)) for r, t in tags.values()]
    result = claude_call.generate(system=PROMPT_PATH.read_text(), user="\n".join(lines), schema=SCHEMA,
                                  label=f"archive plan: {a['title'][:40]}", model=model)

    def pick(aid):
        return tags[aid][0] if aid in tags else None

    deps = [{**tags[d["article_id"]][0], "reason": d.get("reason", "")}
            for d in result.get("dependents") or [] if d.get("article_id") in tags]
    redirect = pick(result.get("redirect_to"))
    if redirect and is_release_note(redirect):
        redirect = None
    runner = pick(result.get("runner_up"))
    if runner and (is_release_note(runner) or (redirect and runner["article_id"] == redirect["article_id"])):
        runner = None
    return {"redirect": redirect, "runner_up": runner, "reason": result.get("reason", ""),
            "dependents": [d for d in deps if not is_release_note(d)]}


def plan_for(change_note, archived_id, live_html, workspace, skip_ids=(), model=MODEL):
    """gather() + choose(): the full recommendation record for results.json."""
    facts = gather(archived_id, live_html, workspace, skip_ids)
    picked = choose(change_note, facts, model=model)
    slim = lambda r: r and {k: r[k] for k in ("article_id", "title", "url", "category_path")}
    return {
        "redirect": slim(picked["redirect"]), "runner_up": slim(picked["runner_up"]), "reason": picked["reason"],
        "dependents": [{**slim(d), "reason": d["reason"]} for d in picked["dependents"]],
        "unresolved_links": facts["unresolved"],
        "mentioned_by": [{**slim(r), "release_note": is_release_note(r)} for r in facts["mentioned_by"]],
        "archived_url": facts["archived"]["url"],
    }


def repoint_instruction(archived_title, archived_url, redirect):
    """The extra instruction for assessing an approved article that links
    to or mentions an article being archived."""
    if redirect:
        return (f"Also: the article \"{archived_title}\" ({archived_url}) is being archived because of this "
                f"change. Wherever this article links to it or tells readers to see it, point that link or "
                f"reference to \"{redirect['title']}\" ({redirect['url']}) instead, if that still makes sense "
                "in the sentence; otherwise remove the reference. Keep every other link as it is.")
    return (f"Also: the article \"{archived_title}\" ({archived_url}) is being archived because of this change, "
            "with no replacement. Remove links to it and references telling readers to see it, keeping the "
            "surrounding text grammatical. Keep every other link as it is.")

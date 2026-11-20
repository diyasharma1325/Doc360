"""Discovery, agent mode, step 1: a plain-text copy of the knowledge base
on disk, one file per published article, so a Claude agent with read-only
Grep / Glob / Read tools can search it the way Claude Code searches code.

Why it exists: triage today sees a title plus a ~30-word snippet per
article and has no tools, so it can't open an article to check. On the
Launchers answer key it dropped 6 of the 27 affected articles it was
shown, mostly FAQs and troubleshooting articles whose snippet didn't look
affected (2026-11-09). An agent that can read the whole article doesn't
have that blind spot.

    python3 doc_sync/kb_mirror.py export     # from knowledge.db; seconds, no network
    python3 doc_sync/kb_mirror.py status

Built FROM the local index (kb_index.py), not from Document360: no API
calls, and the copy is exactly as fresh as the index. The index stores
flattened text, so headings and list structure are not marked in the copy.
Fine for search; if agent mode earns its place, render the HTML to
Markdown during `kb_index build` instead.

Layout: data/kb_mirror/<workspace>/<category path>/<slug>.md, each file
headed by its title, article id, version id, category path and URL. When
the index has screenshot text (OCR, kb_index.py), it follows the article
text under "## Screenshot text", one line per image with the image's
number and the step it illustrates, so an agent can tell an article whose
screenshots still show the old UI.
The whole folder is replaced on every export (all or nothing, like the
index), so an article removed from the index disappears from the copy.

Read-only against the index; writes only data/kb_mirror/ (git-ignored),
or $KB_MIRROR_PATH.
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR.parent / "core"))

import kb_index

DEFAULT_MIRROR_PATH = Path(os.environ.get("KB_MIRROR_PATH") or THIS_DIR / "data" / "kb_mirror")
INFO_FILE = "MIRROR_INFO.json"
MANIFEST_FILE = "manifest.json"  # {article_id: "<workspace>/<category path>/<slug>.md"}

_UNSAFE = re.compile(r'[\\/:*?"<>|\x00-\x1f]+')


def _safe(name):
    """A category or file name usable as one path segment."""
    name = _UNSAFE.sub("-", (name or "").strip()).strip(" .-")
    return name[:80] or "untitled"


def _slug(url, title):
    tail = (url or "").rstrip("/").rsplit("/", 1)[-1]
    return _safe(tail or title)


def _reflow(body):
    """Rejoin text that get_text("\\n") split at inline elements: a link or
    bold label inside a sentence ("see \\nCreate a Launcher\\n.") ends up on
    its own line, which breaks a grep for the sentence. A line that ends in
    whitespace, or a next line that starts with closing punctuation, is the
    same sentence continuing."""
    out = []  # raw lines: the trailing / leading space IS the signal, so strip only at the end
    for line in body.split("\n"):
        prev = out[-1] if out else ""
        if prev.strip() and line.strip() and (prev[-1].isspace() or line[0].isspace() or line[0] in ".,;:)!?"):
            sep = "" if line.lstrip()[0] in ".,;:)!?" else " "
            out[-1] = prev.rstrip() + sep + line.strip()
        else:
            out.append(line)
    return "\n".join(l.rstrip() for l in out)


def _screens_section(screens, images):
    """The "## Screenshot text" block: "- Screenshot 3 (step: ...): <text>"."""
    if not screens:
        return ""
    steps = {i["n"]: i["step_text"] for i in images or []}
    lines = ["", "## Screenshot text", "",
             "Text read from the article's screenshots (OCR; may contain reading errors):", ""]
    for line in screens.split("\n"):
        m = re.match(r"Screenshot (\d+): (.*)", line)
        if not m:
            continue
        step = steps.get(int(m.group(1))) or ""
        where = f" (step: {step[:160]})" if step else ""
        lines.append(f"- Screenshot {m.group(1)}{where}: {m.group(2)}")
    return "\n".join(lines) + "\n"


def render(row, images=None):
    head = [
        f"# {row['title']}",
        "",
        f"- article_id: {row['article_id']}",
        f"- version_id: {row['version_id']}",
        f"- workspace: {row['workspace']}",
        f"- category: {row['category_path']}",
        f"- url: {row['url']}",
        "",
        "---",
        "",
    ]
    screens = row["screens"] if "screens" in row.keys() else ""
    return "\n".join(head) + _reflow(row["body"]) + "\n" + _screens_section(screens, images)


def export(db_path=kb_index.DEFAULT_DB_PATH, out_dir=DEFAULT_MIRROR_PATH):
    st = kb_index.status(db_path)
    if not st.get("exists") or "error" in st:
        raise SystemExit(f"No usable knowledge index at {db_path}: {st}. Build it first: python3 doc_sync/kb_index.py build")

    screens_on = kb_index.has_screens(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    images = {}
    try:
        rows = conn.execute(
            "SELECT title, category_path, body, article_id, version_id, workspace, url"
            + (", screens" if screens_on else "") + " FROM articles").fetchall()
        if screens_on:
            for r in conn.execute("SELECT article_id, n, step_text FROM images"):
                images.setdefault(r["article_id"], []).append({"n": r["n"], "step_text": r["step_text"]})
    finally:
        conn.close()

    out_dir = Path(out_dir)
    tmp = out_dir.with_name(out_dir.name + ".building")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    used, manifest = set(), {}
    for row in rows:
        parts = [_safe(row["workspace"])] + [_safe(p) for p in (row["category_path"] or "").split(" > ") if p.strip()]
        folder = tmp.joinpath(*parts)
        name = _slug(row["url"], row["title"])
        path = folder / f"{name}.md"
        if path in used:  # same slug twice in one category: keep both
            path = folder / f"{name}-{row['article_id'][:8]}.md"
        used.add(path)
        folder.mkdir(parents=True, exist_ok=True)
        path.write_text(render(row, images.get(row["article_id"])), encoding="utf-8")
        manifest[row["article_id"]] = path.relative_to(tmp).as_posix()

    info = {"index_built_at": st["built_at"], "screens_updated_at": st.get("screens_updated_at"),
            "articles": len(rows), "per_workspace": st["per_workspace"],
            "body_includes": st["body_includes"], "screens_includes": st.get("screens_includes"),
            "headings_marked": False}
    (tmp / MANIFEST_FILE).write_text(json.dumps(manifest, indent=0) + "\n", encoding="utf-8")
    (tmp / INFO_FILE).write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    tmp.rename(out_dir)
    return info


def status(out_dir=DEFAULT_MIRROR_PATH, db_path=kb_index.DEFAULT_DB_PATH):
    """{exists, ..., in_sync_with_index}. Never raises."""
    info_path = Path(out_dir) / INFO_FILE
    if not info_path.exists():
        return {"exists": False}
    try:
        info = json.loads(info_path.read_text())
    except (OSError, ValueError) as exc:
        return {"exists": True, "error": f"{type(exc).__name__}: {exc}"}
    st = kb_index.status(db_path)
    # Screenshot text can be filled in place after a build (screenshots.py ocr),
    # so the copy is in sync only when it has both the build and that update.
    in_sync = (st.get("built_at") == info.get("index_built_at")
               and st.get("screens_updated_at") == info.get("screens_updated_at", st.get("screens_updated_at")))
    return {"exists": True, **info, "in_sync_with_index": in_sync}


def ensure_fresh(out_dir=DEFAULT_MIRROR_PATH, db_path=kb_index.DEFAULT_DB_PATH):
    """Re-export when the copy is missing or older than the index (seconds,
    no network), so agent discovery never searches a stale copy."""
    st = status(out_dir, db_path)
    if not st.get("in_sync_with_index"):
        print("    (knowledge base copy missing or out of date — re-exporting it from the index)")
        export(db_path, out_dir)


def manifest(out_dir=DEFAULT_MIRROR_PATH):
    return json.loads((Path(out_dir) / MANIFEST_FILE).read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("export")
    sub.add_parser("status")
    args = p.parse_args()
    if args.cmd == "export":
        info = export()
        print(f"Exported {info['articles']} articles to {DEFAULT_MIRROR_PATH} (index built {info['index_built_at']})")
    else:
        print(json.dumps(status(), indent=2))


if __name__ == "__main__":
    main()

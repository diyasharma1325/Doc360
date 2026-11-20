"""Phase 2's screenshot step: judge an article's screenshots against the
change, find replacements among images already known to show the new UI,
and check the retakes a writer supplies.

Three vision calls, all through claude -p (claude_call.py) with only the
Read tool, in a temporary folder OUTSIDE the repo holding just the images
(so no CLAUDE.md is loaded and the model can read nothing else):

1. REVIEW (review_article): every image of one article, with the change
   note, its UI facts and each image's step text and alt text. Verdict per
   image: stale / fine / unsure, what is visible, why, and retake
   instructions for a stale one. A fine image that visibly shows the
   changed area in its NEW state is recorded as current, which is what
   later suggestions draw on.
2. COMPARE (_compare): one stale image against up to MAX_CANDIDATES
   replacements -> drop_in (same screen, same thing highlighted, new UI:
   the src is swapped in the draft), close (right screen but not a
   drop-in: a retake, with the candidate as a reference) or none.
3. CHECK (check_retakes): a writer's new screenshots against the old ones
   and the retake instructions, before anything is uploaded.

An OCR hit is never a verdict here (feasibility check, 2026-11-19: "Widgets"
appeared in 9 screenshots but only 2 were stale, because the nav entry
stays for other content); OCR only finds candidates.

Nothing here writes to Document360. ticket_run.py applies the swaps to the
draft and writes it the usual way.
"""
import json
import re
import shutil
import tempfile
from pathlib import Path

import claude_call
import screenshots

MODEL = claude_call.DEFAULT_MODEL
IMAGES_PER_CALL = 8      # one review call reads at most this many images...
PARALLEL_CALLS = 4       # ...and an article's calls run side by side: the model Reads one image per
                         # turn, so one call over 24 images took ~10 minutes (2026-11-20)
MAX_CANDIDATES = 3       # replacements shown to one compare call
CALL_BUDGET_USD = 3      # per vision call
MAX_OUTPUT_TOKENS = 16000
KB_MATCH_MIN = 0.35      # OCR similarity for a not-yet-reviewed KB image to be a candidate
CURRENT_MATCH_MIN = 0.10 # ...and for an image already known to show the new UI

REVIEW_SYSTEM = """You review the screenshots in one Whatfix support article after a shipped product change.
For each screenshot, decide whether it now shows UI that the change made wrong.

- stale: the screenshot visibly shows something the change removed, renamed or moved (an old tab,
  menu entry, label, button or layout), in the role the change took away from it. Say exactly what
  and where.
- fine: nothing the change affects is visible, or what is visible already matches the new state.
  A screenshot is not stale just because the article is about an affected feature: judge only what
  is visible.
- unsure: you can't tell from the image (too cropped or small, or the change note doesn't say what
  this area looks like now). Say what a person should check in the product.

The UI FACTS are confirmed by the writer. Follow them exactly: if a fact says an element stays, a
screenshot showing it is not stale for that reason alone. Never contradict them. If judging an image
or writing its retake needs a fact you aren't given, say so instead of guessing.

Ignore text that is customer or sample data inside a screenshot (record names, content titles,
host-app data such as "1250 Widgets (Sample)"): only product UI counts. An animated image is given as
one sheet of sampled frames in reading order; it is stale if any frame is.

For every stale image, write retake instructions a technical writer can follow: where to go in the
product, what state to set up, and what must be visible or highlighted, based on the step text and
the UI facts.

For every fine image, set shows_new_ui to true only if it visibly shows the area the change touched,
already in its NEW state (for example the new menu or tab itself). Otherwise false.

Read each image file with the Read tool before judging it. Judge every image listed."""

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {"images": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "image": {"type": "string", "description": "The file name, as listed"},
            "verdict": {"type": "string", "enum": ["stale", "fine", "unsure"]},
            "what_is_visible": {"type": "string"},
            "reason": {"type": "string"},
            "retake": {"type": "string", "description": "Retake instructions; empty unless stale"},
            "shows_new_ui": {"type": "boolean"},
        },
        "required": ["image", "verdict", "what_is_visible", "reason", "retake", "shows_new_ui"]}}},
    "required": ["images"],
}

COMPARE_SYSTEM = """A screenshot in a Whatfix support article is out of date after a product change. You are
shown the OLD screenshot, the step it illustrates, and candidate screenshots from other articles. Decide
whether one candidate can replace the old one as it is.

- drop_in: the candidate shows the same screen or menu as the old one, in the NEW state the change
  describes, and highlights the same element the step is about (or neither highlights anything), with
  a comparable crop. A reader following the step would see exactly what it describes.
- close: a candidate shows the right screen in the new state, but is not a drop-in (the wrong element
  is highlighted or marked, the crop is very different, or it shows a different item). It is still a
  useful reference for a retake.
- none: no candidate shows the right screen in the new state.

Follow the UI facts exactly. Judge only what is visible; ignore customer or sample data. Read every
image file with the Read tool before deciding. For drop_in, write alt text for the candidate as it will
be used in this article: name the screen and what is highlighted, in under 15 words, without repeating
the step's wording."""

COMPARE_SCHEMA = {
    "type": "object",
    "properties": {
        "choice": {"type": "string", "enum": ["drop_in", "close", "none"]},
        "candidate": {"type": "string", "description": "The chosen candidate's file name; empty for none"},
        "reason": {"type": "string"},
        "alt_text": {"type": "string", "description": "For drop_in only; else empty"},
    },
    "required": ["choice", "candidate", "reason", "alt_text"],
}

CHECK_SYSTEM = """A technical writer has retaken out-of-date screenshots in a Whatfix support article after a
product change. For each pair you get the OLD screenshot, the NEW one, the step it illustrates and the
retake instructions. Decide whether the new screenshot can go into the article.

- ok: it shows the NEW state the change describes (follow the UI facts exactly), it shows the screen
  the step is about, and what the instructions say must be visible or highlighted is.
- not ok: it still shows the old UI, shows a different screen, misses what must be highlighted, or is
  unreadable. Say exactly what is wrong so the writer can retake it.

Read every image file with the Read tool before deciding. Judge only product UI, not sample data. For
every new screenshot, also write alt text (the screen and what is highlighted, under 15 words, without
repeating the step) and a file name of the form Place_Action_Element (for example
Guidance_Dashboard_Click_Content, Whatfix_Studio_Select_Blocker): letters, digits and underscores only."""

CHECK_SCHEMA = {
    "type": "object",
    "properties": {"images": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "image": {"type": "string", "description": "The NEW file's name, as listed"},
            "ok": {"type": "boolean"},
            "reason": {"type": "string"},
            "alt_text": {"type": "string"},
            "filename": {"type": "string"},
        },
        "required": ["image", "ok", "reason", "alt_text", "filename"]}}},
    "required": ["images"],
}


# --- helpers ----------------------------------------------------------------------

def _facts_block(note):
    lines = ["CHANGE NOTE", f"Summary: {note.summary}", f"Old: {note.old}", f"New: {note.new}"]
    if note.notes:
        lines.append(f"Notes: {note.notes}")
    for c in note.changes or []:
        lines.append(f"- {c.content_type}: {c.old!r} -> {c.new!r}")
    if note.all_old_terms():
        lines.append("Old terms: " + ", ".join(note.all_old_terms()))
    if note.ui_facts:
        lines.append("UI FACTS (confirmed; follow exactly):")
        lines += [f"- {f}" for f in note.ui_facts]
    else:
        lines.append("UI FACTS: none given. Where a verdict or retake depends on one, say what to check.")
    return "\n".join(lines)


def _vision_call(system, user, schema, files, label):
    """One claude -p call that may Read only `files` ({name: local path}),
    copied into a temporary folder outside the repo."""
    tmp = Path(tempfile.mkdtemp(prefix="doc_sync_images_"))
    try:
        for name, src in files.items():
            shutil.copyfile(src, tmp / name)
        return claude_call.generate(system=system, user=user, schema=schema, label=label, model=MODEL,
                                    max_tokens=MAX_OUTPUT_TOKENS, tools=["Read"], cwd=str(tmp),
                                    budget_usd=CALL_BUDGET_USD)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


_WORD_RE = re.compile(r"[a-z][a-z0-9]{2,}")


def _tokens(text):
    return set(_WORD_RE.findall((text or "").lower()))


def _similarity(a, b):
    a, b = _tokens(a), _tokens(b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _signed_src(path, article_id, client, cache):
    """A downloadable (freshly signed) src for the image at `path`, read
    from the article that shows it. None if it isn't there any more."""
    if not article_id:
        return None
    if article_id not in cache:
        try:
            cache[article_id] = screenshots.article_images(client.get_article(article_id)["data"]
                                                           .get("html_content") or "")
        except Exception:
            cache[article_id] = []
    for im in cache[article_id]:
        if im["path"] == path:
            return im["src"]
    return None


# --- 1. review ------------------------------------------------------------------

def review_article(note, title, html_content, frames_dir, article_id="", run=None, log=print):
    """Review every image in `html_content`. Saves each image, prepared for
    vision, to `frames_dir` (<n>.png, kept for the artifact and the writer).
    Returns {"reviewed": int, "items": [...]}, one item per distinct image:
    {n, ns, path, src, alt, step_text, file, frames, ocr, verdict,
    what_is_visible, reason, retake, shows_new_ui, status}. `status` starts
    as fine / unsure / retake. Raises claude_call.ClaudeCallError."""
    frames_dir = Path(frames_dir)
    images = screenshots.article_images(html_content)
    items, by_path = [], {}
    for im in images:
        if not im["path"]:
            continue
        if im["path"] in by_path:
            by_path[im["path"]]["ns"].append(im["n"])
            continue
        item = {**im, "ns": [im["n"]]}
        try:
            data = screenshots.fetch(im["src"])
            item["file"], item["frames"] = screenshots.prepare(data, frames_dir, f"{im['n']:03d}")
            item["ocr"] = screenshots.ocr(data) if screenshots.tesseract_available() else ""
        except Exception as exc:
            item.update(file=None, frames=0, ocr="", verdict="unsure", what_is_visible="",
                        reason=f"The image could not be downloaded or read ({type(exc).__name__}).",
                        retake="", shows_new_ui=False)
        by_path[im["path"]] = item
        items.append(item)

    todo = [i for i in items if i.get("file")]
    chunks = [todo[k:k + IMAGES_PER_CALL] for k in range(0, len(todo), IMAGES_PER_CALL)]
    if len(chunks) > 1 and len(chunks[-1]) < 3:
        chunks[-2] += chunks.pop()

    def review_chunk(chunk):
        lines = []
        for i in chunk:
            kind = (f"animated, {i['frames']} frames, shown as one sheet of 4 sampled frames"
                    if i["frames"] > 1 else "still")
            lines.append(f"- {i['file']} (image {i['n']}, {kind})\n  alt text: {i['alt'] or '(none)'}\n"
                         f"  step text before it: {i['step_text'] or '(none)'}")
        user = (_facts_block(note) + f"\n\nARTICLE: {title}\n\nSCREENSHOTS (files in the current folder):\n"
                + "\n".join(lines))
        return _vision_call(REVIEW_SYSTEM, user, REVIEW_SCHEMA,
                            {i["file"]: frames_dir / i["file"] for i in chunk},
                            label=f"screenshot review: {title[:40]}")

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=PARALLEL_CALLS) as pool:
        answers = list(pool.map(review_chunk, chunks))  # re-raises the first failed call
    for chunk, result in zip(chunks, answers):
        got = {r["image"].strip(): r for r in result.get("images") or []}
        for i in chunk:
            r = got.get(i["file"])
            if not r:
                i.update(verdict="unsure", what_is_visible="", reason="The review returned no verdict for it.",
                         retake="", shows_new_ui=False)
            else:
                i.update(verdict=r["verdict"], what_is_visible=r["what_is_visible"], reason=r["reason"],
                         retake=r["retake"] if r["verdict"] == "stale" else "",
                         shows_new_ui=bool(r.get("shows_new_ui")) and r["verdict"] == "fine")
    for i in items:
        i["status"] = {"stale": "retake", "fine": "fine"}.get(i["verdict"], "unsure")

    screenshots.record_verdicts(note.feature_area, article_id, items, run=run)
    conn = screenshots.connect()
    try:
        for i in items:
            if i.get("file") and screenshots.tesseract_available():
                conn.execute("INSERT OR IGNORE INTO ocr (path, text, at) VALUES (?, ?, ?)",
                             (i["path"], i["ocr"], screenshots._now()))
        conn.commit()
    finally:
        conn.close()
    for i in items:
        if i.get("shows_new_ui"):
            screenshots.record_current(note.feature_area, i["path"], i["path"], "reviewed", article_id, title,
                                       i["n"], i["what_is_visible"], run=run)
    stale = sum(1 for i in items if i["verdict"] == "stale")
    log(f"      screenshots: {len(items)} reviewed, {stale} stale, "
        f"{sum(1 for i in items if i['verdict'] == 'unsure')} unsure")
    return {"reviewed": len(items), "items": items}


# --- 2. replacements -------------------------------------------------------------

def _candidates(note, item, article_id, kb_db=None):
    """Up to MAX_CANDIDATES replacement candidates for one stale image, best
    first: [{path, article_id, title, image_n, source, score}]. First images
    already known to show this change's new UI, then indexed images whose
    screenshot text is close to this one's."""
    import kb_index

    kb_db = kb_db or kb_index.DEFAULT_DB_PATH
    stale_text = item.get("ocr") or ""
    seen, out = {item["path"]}, []
    current = []
    for c in screenshots.current_images(note.feature_area):
        if c["path"] in seen or c.get("article_id") == article_id:
            continue
        cand_ocr = screenshots.cached_ocr([c["path"]]).get(c["path"], "")
        score = max(_similarity(stale_text, cand_ocr),
                    _similarity(item.get("what_is_visible", "") + " " + item.get("step_text", ""),
                                c.get("description") or ""))
        if score >= CURRENT_MATCH_MIN:
            current.append({**c, "score": round(score, 3)})
    for c in sorted(current, key=lambda c: -c["score"])[:MAX_CANDIDATES]:
        seen.add(c["path"])
        out.append(c)

    if len(out) < MAX_CANDIDATES and stale_text and kb_index.has_screens(kb_db):
        stale_paths = set()
        conn = screenshots.connect()
        try:
            for r in conn.execute("SELECT path FROM verdicts WHERE feature_area = ? AND verdict != 'fine'",
                                  (note.feature_area,)):
                stale_paths.add(r["path"])
            rows = conn.execute("SELECT path, text FROM ocr WHERE text != ''").fetchall()
        finally:
            conn.close()
        scored = []
        for r in rows:
            if r["path"] in seen or r["path"] in stale_paths:
                continue
            score = _similarity(stale_text, r["text"])
            if score >= KB_MATCH_MIN:
                scored.append((score, r["path"]))
        for score, path in sorted(scored, reverse=True):
            if len(out) >= MAX_CANDIDATES:
                break
            where = [w for w in kb_index.where_image(path, kb_db) if w["article_id"] != article_id]
            if not where:
                continue
            seen.add(path)
            out.append({"path": path, "article_id": where[0]["article_id"], "title": where[0]["title"],
                        "image_n": where[0]["n"], "source": "kb", "score": round(score, 3)})
    return out


def _compare(note, item, cands, frames_dir, client, src_cache, title):
    """Run the compare call for one stale image. Returns (decision, the
    chosen candidate or None)."""
    reuse_dir = Path(frames_dir) / "candidates"
    files = {"old.png": Path(frames_dir) / item["file"]}
    listed = []
    for k, c in enumerate(cands, 1):
        src = _signed_src(c["path"], c.get("article_id"), client, src_cache)
        if not src and str(c.get("src", "")).startswith("http") and "?" in c["src"]:
            src = c["src"]
        if not src:
            continue
        try:
            name, _ = screenshots.prepare(screenshots.fetch(src), reuse_dir, f"{item['n']:03d}-c{k}")
        except Exception:
            continue
        c["file"] = f"candidates/{name}"
        files[f"candidate{k}.png"] = reuse_dir / name
        listed.append((f"candidate{k}.png", c))
    if not listed:
        return {"choice": "none", "candidate": "", "reason": "No candidate could be downloaded.", "alt_text": ""}, None
    user = (_facts_block(note) + f"\n\nARTICLE: {title}\nOLD screenshot: old.png (image {item['n']})\n"
            f"What it shows: {item.get('what_is_visible') or '(not described)'}\n"
            f"Why it is out of date: {item.get('reason') or ''}\n"
            f"Step text before it: {item.get('step_text') or '(none)'}\n\nCANDIDATES:\n"
            + "\n".join(f"- {name}: from \"{c.get('title') or 'another article'}\""
                        + (f", image {c['image_n']}" if c.get("image_n") else "") for name, c in listed))
    decision = _vision_call(COMPARE_SYSTEM, user, COMPARE_SCHEMA, files,
                            label=f"screenshot reuse: {title[:30]} #{item['n']}")
    chosen = dict(listed).get((decision.get("candidate") or "").strip())
    if decision.get("choice") in ("drop_in", "close") and not chosen:
        decision = {**decision, "choice": "none", "reason": "The answer named no listed candidate."}
    return decision, chosen


def suggest_replacements(note, review, title, frames_dir, client, article_id="", log=print):
    """For each stale image in `review`, look for a replacement. A drop-in
    becomes a swap (status "reused", with `reuse`); a close one stays a
    retake with the candidate as `reference`. Updates `review` in place and
    returns the swaps: [{path, new_src, alt}]. A failed lookup leaves the
    image a retake; it never raises."""
    swaps, src_cache = [], {}
    for item in review["items"]:
        if item["verdict"] != "stale" or not item.get("file"):
            continue
        try:
            cands = _candidates(note, item, article_id)
            if not cands:
                continue
            decision, chosen = _compare(note, item, cands, frames_dir, client, src_cache, title)
        except Exception as exc:
            log(f"      (replacement lookup for image {item['n']} failed: {type(exc).__name__}: {str(exc)[:120]})")
            continue
        info = None
        if chosen:
            info = {"path": chosen["path"], "article_id": chosen.get("article_id"), "title": chosen.get("title"),
                    "image_n": chosen.get("image_n"), "source": chosen.get("source"), "file": chosen.get("file"),
                    "reason": decision.get("reason", "")}
        if decision["choice"] == "drop_in" and info:
            item["status"] = "reused"
            item["reuse"] = {**info, "alt": decision.get("alt_text") or ""}
            swaps.append({"path": item["path"], "new_src": chosen["path"], "alt": decision.get("alt_text") or None})
            log(f"      image {item['n']}: reused from \"{info['title']}\"")
        elif decision["choice"] == "close" and info:
            item["reference"] = info
    return swaps


# --- 3. the writer's retakes -----------------------------------------------------

def check_retakes(note, title, pairs, work_dir):
    """`pairs`: [{n, old_file (path), new_file (path), step_text, retake}].
    Returns {n: {ok, reason, alt_text, filename}}."""
    files, lines = {}, []
    for p in pairs:
        old_name, new_name = f"old-{p['n']:03d}.png", f"new-{p['n']:03d}.png"
        files[new_name] = p["new_file"]
        if p.get("old_file") and Path(p["old_file"]).exists():
            files[old_name] = p["old_file"]
        else:
            old_name = "(old screenshot not available)"
        lines.append(f"- image {p['n']}: OLD {old_name}, NEW {new_name}\n"
                     f"  step text before it: {p.get('step_text') or '(none)'}\n"
                     f"  retake instructions: {p.get('retake') or '(none given)'}")
    user = _facts_block(note) + f"\n\nARTICLE: {title}\n\nPAIRS (files in the current folder):\n" + "\n".join(lines)
    result = _vision_call(CHECK_SYSTEM, user, CHECK_SCHEMA, files, label=f"retake check: {title[:40]}")
    out = {}
    for r in result.get("images") or []:
        m = re.search(r"new-(\d+)", r.get("image") or "")
        if m:
            out[int(m.group(1))] = r
    return out


def clean_filename(name, fallback):
    name = re.sub(r"[^A-Za-z0-9_]+", "_", (name or "").strip()).strip("_")[:80]
    return (name or fallback) + ".png"


def save_review(path, review):
    Path(path).write_text(json.dumps(review, indent=1))

"""Screenshots in a ticket run: phase 2's review of each approved article's
screenshots, the comment section that reports it, and the writer's step
that brings in retakes (ticket_run.py `screenshots`).

Phase 2 (review_for_phase2), per approved article:
  1. Review every screenshot (image_review.review_article): fine, unsure,
     or stale with retake instructions.
  2. For each stale one, look for a replacement already known to show the
     new UI; a drop-in is swapped into the draft straight away (status
     "reused"), a near miss stays a retake with the candidate as a
     reference.
  The draft carries the text edit (if any) and the swaps; nothing is ever
  written to a live article.

The screenshots step (run_screenshots), once the writer has:
  - saved retakes as runs/<run>/screenshots/<plan #>/<image #>.png
    (e.g. screenshots/3/010.png; the I2P extension's Free Capture -> Download
    all gives framed PNGs, the house style since 2026-11-20),
  - and/or marked images: `--fine 3:12` (checked, keep it as it is) or
    `--reject 3:1` (undo a reused screenshot: it becomes a retake).
  Each retake is checked (PNG, size, then a vision check against the old
  screenshot and the retake instructions), uploaded to Document360 Drive,
  swapped into the draft, and the draft is written again the usual way.
  `--check-only` stops before anything is uploaded or written.

Item statuses: fine, unsure, retake, reused (swapped from another
article), replaced (writer's retake, uploaded), kept (writer said fine).
"""
import json
import re
import time
from pathlib import Path

import claude_call
import image_review
import screenshots
import ticket

PENDING = ("retake", "unsure")
SPEC_RE = re.compile(r"^\s*(\d+)\s*[:#/.-]\s*(\d+)\s*$")

_KEEP = ("n", "ns", "path", "alt", "step_text", "file", "frames", "verdict", "what_is_visible", "reason",
         "retake", "status", "reuse", "reference")


def _compact(review, stem):
    """The review as stored in results.json: files relative to out/."""
    items = []
    for i in review["items"]:
        c = {k: i[k] for k in _KEEP if k in i}
        if c.get("file"):
            c["file"] = f"images/{stem}/{c['file']}"
        for key in ("reuse", "reference"):
            if c.get(key, {}).get("file"):
                c[key] = {**c[key], "file": f"images/{stem}/{c[key]['file']}"}
        items.append(c)
    return {"reviewed": review["reviewed"], "items": items}


def review_for_phase2(rd, note, a, html_content, client, stem, log=print):
    """(images record for results.json, swaps [{path, new_src, alt}]).
    Raises claude_call.ClaudeCallError when the review call fails."""
    frames_dir = Path(rd) / "out" / "images" / stem
    review = image_review.review_article(note, a["title"], html_content, frames_dir, a["article_id"],
                                         run=Path(rd).name, log=log)
    swaps = image_review.suggest_replacements(note, review, a["title"], frames_dir, client, a["article_id"],
                                              log=log)
    image_review.save_review(frames_dir / "review.json", review)
    return _compact(review, stem), swaps


def apply_swaps(html_content, swaps):
    out = html_content
    for s in swaps:
        out, _ = screenshots.swap_src(out, s["path"], s["new_src"], s.get("alt"))
    return out


def swaps_of(images):
    """{old path: new src} for every image the draft replaces."""
    out = {}
    for i in (images or {}).get("items") or []:
        if i["status"] == "reused":
            out[i["path"]] = i["reuse"]["path"]
        elif i["status"] == "replaced":
            out[i["path"]] = i["new_src"]
    return out


def pending(images):
    return [i for i in (images or {}).get("items") or [] if i["status"] in PENDING]


# --- the comment section ---------------------------------------------------------

def _num(i):
    return f"{i['n']:03d}"


def comment_section(rows):
    """Lines for the phase 2 (or screenshots) comment: per article what was
    checked, then what the writer has to do."""
    rows = [r for r in rows if r.get("images") or r.get("images_error")]
    if not rows:
        return []
    lines = ["**Screenshots.** I checked every screenshot in each article against the change.", ""]
    retakes, unsure, reused = [], [], []
    for r in rows:
        if r.get("images_error"):
            lines.append(f"- **#{r['n']} {r['title']}**: the screenshot check failed "
                         f"(`{r['images_error'][:200]}`); run phase 2 again to retry it.")
            continue
        items = r["images"]["items"]
        counts = {s: sum(1 for i in items if i["status"] == s)
                  for s in ("fine", "kept", "reused", "replaced", "retake", "unsure")}
        parts = [f"{counts['fine'] + counts['kept']} fine"]
        parts += [f"{counts[s]} {label}" for s, label in (("reused", "replaced from another article"),
                                                          ("replaced", "replaced with your retake"),
                                                          ("retake", "to retake"), ("unsure", "to check"))
                  if counts[s]]
        lines.append(f"- **#{r['n']} {r['title']}**: {r['images']['reviewed']} checked: " + ", ".join(parts) + ".")
        for i in items:
            if i["status"] == "retake":
                retakes.append((r, i))
            elif i["status"] == "unsure":
                unsure.append((r, i))
            elif i["status"] == "reused":
                reused.append((r, i))
    if reused:
        lines += ["", "**Replaced from another article** (already in the draft; please confirm each one):", ""]
        for r, i in reused:
            u = i["reuse"]
            lines.append(f"- #{r['n']} image {i['n']}: now shows image {u.get('image_n') or '?'} from "
                         f"\"{u.get('title') or 'another article'}\". {u.get('reason') or ''} "
                         f"To undo it, reply `reject {r['n']}:{i['n']}`.".replace("  ", " "))
    if retakes:
        lines += ["", "**To retake.** Save each new screenshot as a PNG at the path shown (the I2P extension's "
                  "Free Capture, then Download all, gives the house frame):", ""]
        for r, i in retakes:
            ref = ""
            if i.get("reference"):
                ref = (f" A close match to start from: image {i['reference'].get('image_n') or '?'} in "
                       f"\"{i['reference'].get('title')}\".")
            problem = f" ⚠ Last attempt: {i['retake_problem']}" if i.get("retake_problem") else ""
            lines.append(f"- `screenshots/{r['n']}/{_num(i)}.png`, #{r['n']} image {i['n']}: "
                         f"{i.get('retake') or i.get('reason')}{ref}{problem}")
    if unsure:
        lines += ["", "**To check in the product** (I couldn't tell from the screenshot):", ""]
        for r, i in unsure:
            lines.append(f"- #{r['n']} image {i['n']}: {i.get('reason')} If it's fine as it is, reply "
                         f"`fine {r['n']}:{i['n']}`; if not, save a retake at `screenshots/{r['n']}/{_num(i)}.png`.")
    if retakes or unsure or reused:
        lines += ["", "When the retakes are saved, run the **screenshots** step: it checks each one, uploads "
                  "it to Document360 Drive and puts it in the draft."]
    lines.append("")
    return lines


# --- the screenshots step ----------------------------------------------------------

class ScreenshotsRefused(RuntimeError):
    pass


def parse_specs(text):
    """"3:12, 3:1" -> {(3, 12), (3, 1)}."""
    out = set()
    for part in re.split(r"[,\s]+(?=\d)", (text or "").strip()):
        if not part.strip():
            continue
        m = SPEC_RE.match(part)
        if not m:
            raise ScreenshotsRefused(f"{part!r} isn't <plan #>:<image #>, e.g. 3:12.")
        out.add((int(m.group(1)), int(m.group(2))))
    return out


def _retake_files(rd, n):
    """{image number: path} for the PNGs saved under screenshots/<n>/."""
    folder = Path(rd) / "screenshots" / str(n)
    out = {}
    if folder.is_dir():
        for f in sorted(folder.iterdir()):
            m = re.match(r"\D*(\d+)", f.stem)
            if f.is_file() and m and not f.name.startswith("."):
                out[int(m.group(1))] = f
    return out


def run_screenshots(run, fine=(), reject=(), archived_links=None, confirm_overwrite=False, check_only=False,
                    client=None, upload=None, log=print):
    """The writer's screenshots step. Returns {article n: summary}. See the
    module docstring."""
    import d360_drive
    import ticket_run
    import verify

    rd = ticket.run_dir(run)
    tk = ticket.load_ticket(rd)
    if tk.get("status") != ticket.FOR_REVIEW:
        raise ScreenshotsRefused(f"{tk['key']} is in {tk.get('status')!r}; the screenshots step runs in For review.")
    results = ticket_run.load_results(rd)
    approved = ticket_run.load_approved(rd) or {"articles": []}
    rows = {r["n"]: r for r in results["articles"].values() if r.get("images")}
    if not rows:
        raise ScreenshotsRefused("No article in this run has reviewed screenshots: run phase 2 first.")
    unknown = [f"{n}:{i}" for n, i in set(fine) | set(reject)
               if n not in rows or not any(i in it["ns"] for it in rows[n]["images"]["items"])]
    if unknown:
        raise ScreenshotsRefused("Not a reviewed screenshot in this run: " + ", ".join(sorted(unknown)))
    note = ticket_run.load_change_note(str(rd / "change_note.json"))
    if upload is None and not check_only:
        missing = d360_drive.configured()
        if missing:
            raise ScreenshotsRefused(f"Can't upload to Document360 Drive: {missing} not set in .env.")
        upload = d360_drive.upload_png
    if client is None:
        from d360_client import Document360Client
        client = Document360Client()

    summary, writes = {}, []
    for n, r in sorted(rows.items()):
        items = r["images"]["items"]
        by_n = {i["n"]: i for i in items}
        for i in items:  # an image listed twice answers to either number
            for k in i["ns"]:
                by_n.setdefault(k, i)
        changed, html_changed, done = False, False, []
        for (sn, si) in sorted(set(fine)):
            if sn == n and by_n[si]["status"] in PENDING:
                by_n[si]["status"] = "kept"
                changed = True
                done.append(f"image {si} kept as it is")
        for (sn, si) in sorted(set(reject)):
            if sn == n and by_n[si]["status"] == "reused":
                it = by_n[si]
                it["rejected_reuse"] = it.pop("reuse")
                it["status"] = "retake"
                if it.get("rejected_reuse"):
                    it["reference"] = {k: v for k, v in it["rejected_reuse"].items() if k != "alt"}
                changed = html_changed = True
                done.append(f"image {si}: reused screenshot undone, now a retake")

        files = _retake_files(rd, n)
        todo = []
        for k, f in files.items():
            it = by_n.get(k)
            if not it or it["status"] in ("replaced", "kept", "fine"):
                continue
            data = f.read_bytes()
            problem = screenshots.check_upload(data)
            if problem:
                it["retake_problem"] = f"{f.name}: {problem}."
                done.append(f"image {k}: {f.name} refused, {problem}")
                changed = True
                continue
            todo.append((it, f, data))
        if todo:
            pairs = [{"n": it["n"], "old_file": rd / "out" / it["file"] if it.get("file") else None,
                      "new_file": f, "step_text": it.get("step_text"),
                      "retake": it.get("retake") or it.get("reason")} for it, f, _ in todo]
            try:
                checked = image_review.check_retakes(note, r["title"], pairs, rd)
            except claude_call.ClaudeCallError as exc:
                raise ScreenshotsRefused(f"The retake check for #{n} failed: {exc}")
            for it, f, data in todo:
                c = checked.get(it["n"])
                if not c or not c.get("ok"):
                    it["retake_problem"] = (c or {}).get("reason") or "the check returned no answer for it"
                    done.append(f"image {it['n']}: retake not accepted, {it['retake_problem']}")
                    changed = True
                    continue
                if check_only:
                    done.append(f"image {it['n']}: retake looks right (not uploaded: check only)")
                    continue
                name = image_review.clean_filename(c.get("filename"), f"{r['title'][:40]}_{it['n']:03d}")
                url, verified = upload(name, data)
                it.update(status="replaced", new_src=url, new_alt=c.get("alt_text") or None, uploaded_name=name,
                          upload_verified=verified, new_file=f.relative_to(rd).as_posix())
                it.pop("retake_problem", None)
                done.append(f"image {it['n']}: retake uploaded as {name}")
                changed = html_changed = True
        summary[n] = done
        if check_only:
            continue
        if html_changed:
            writes.append(r)
        elif changed and r.get("outcome") == "screenshots_pending" and not pending(r["images"]):
            r["outcome"] = "no_edit"  # every screenshot left to do was marked fine
        if changed:
            results["articles"][r["article_id"]] = r

    if check_only:
        return summary

    targets = None
    if archived_links:
        from archived_writer import ArchivedTargets, ArchivedWriteRefused
        targets = ArchivedTargets(archived_links, client=client)
        try:
            targets.describe()
        except ArchivedWriteRefused as exc:
            raise ScreenshotsRefused(str(exc))
        need = [r for r in writes if not r.get("target_id")]
        free = [t for t in targets.describe() if t["id"] not in results["targets_used"]]
        if need and not confirm_overwrite:
            names = "\n".join(f"  - {t['title']!r}  ({t['link']})" for t in free[:len(need)])
            raise ScreenshotsRefused("These Archived articles would be OVERWRITTEN, content and title, with no undo:\n"
                                     f"{names}\nRun again with --confirm-overwrite once the writer has agreed.")

    for r in writes:
        _rewrite_draft(rd, note, r, client, targets, results, verify, log)
        results["articles"][r["article_id"]] = r
        ticket_run._save(rd, "results.json", results)
    ticket_run._save(rd, "results.json", results)
    if writes or any(summary.values()):
        order = [a["article_id"] for a in approved["articles"]]
        shown = sorted((r for r in results["articles"].values() if r.get("images")),
                       key=lambda r: order.index(r["article_id"]) if r["article_id"] in order else r["n"])
        head = ["Screenshots updated:", ""]
        for n, done in sorted(summary.items()):
            if done:
                head.append(f"- **#{n} {rows[n]['title']}**: " + "; ".join(done) + ".")
        for r in writes:
            where = (f"[the Archived draft]({r['target_link']})" if r.get("target_link")
                     else f"`{r.get('after')}`")
            head.append(f"- #{r['n']}: draft updated, {where}.")
        ticket.record_comment(rd, "\n".join(head + [""] + comment_section(shown)), label="screenshots updated")
        ticket.record_event(rd, "screenshots", actor="writer", fine=sorted(f"{a}:{b}" for a, b in fine),
                            reject=sorted(f"{a}:{b}" for a, b in reject), updated=[r["n"] for r in writes])
    return summary


def _rewrite_draft(rd, note, r, client, targets, results, verify, log):
    """Rebuild one article's draft with every swap so far and write it where
    its draft lives (its Archived target, a new one, or the run folder)."""
    import ticket_run

    out = Path(rd) / "out"
    stem = f"{r['n']:02d}-{ticket_run._slug(r['title'])}"
    before_path = out / "articles" / f"{stem}.before.html"
    after_path = out / "articles" / f"{stem}.after.html"
    if r.get("after") and after_path.exists():
        base = after_path.read_text()
        before = before_path.read_text() if before_path.exists() else base
    else:  # no draft yet (screenshots only): start from the live article as it is now
        live = client.get_article(r["article_id"])["data"]
        base = before = live.get("html_content") or ""
        import draft_writer
        if draft_writer.has_pending_draft(live):
            r.update(outcome="merge_conflict",
                     note="The live article already has an unpublished draft; merge the screenshots by hand.")
            return
    html = base
    for it in r["images"]["items"]:
        if it["status"] == "replaced":
            current = it.get("reuse", {}).get("path") or it["path"]
            for old in {it["path"], current, (it.get("rejected_reuse") or {}).get("path")} - {None}:
                html, _ = screenshots.swap_src(html, old, it["new_src"], it.get("new_alt"))
        elif it["status"] == "retake" and it.get("rejected_reuse"):
            html, _ = screenshots.swap_src(html, it["rejected_reuse"]["path"], it["path"], it.get("alt") or None)
    (out / "articles").mkdir(parents=True, exist_ok=True)
    before_path.write_text(before)
    after_path.write_text(html)
    r.update(before=f"articles/{stem}.before.html", after=f"articles/{stem}.after.html")
    swaps = swaps_of(r["images"])
    for it in r["images"]["items"]:
        if it["status"] == "replaced":
            screenshots.record_current(note.feature_area, screenshots.image_path(it["new_src"]), it["new_src"],
                                       "uploaded", r.get("target_id") or r["article_id"], r["title"], it["n"],
                                       it.get("what_is_visible") or it.get("retake") or "", run=Path(rd).name)
        elif it["status"] == "reused":
            screenshots.record_current(note.feature_area, it["reuse"]["path"], it["reuse"]["path"], "reused",
                                       it["reuse"].get("article_id"), it["reuse"].get("title"),
                                       it["reuse"].get("image_n"), it.get("what_is_visible") or "",
                                       run=Path(rd).name)

    target_id, link = r.get("target_id"), r.get("target_link")
    if target_id:
        from archived_writer import ArchivedTargets
        t = ArchivedTargets([link], client=client)
        t.write(target_id, r["title"], html)
        check = verify.verify_article(target_id, note, before, client=t.client, swaps=swaps)
        r.update(outcome="draft_written")
    elif targets is not None:
        free = [t["id"] for t in targets.describe() if t["id"] not in results["targets_used"]]
        if not free:
            r.update(outcome="draft_saved", warnings=["No Archived target left; the draft is saved locally."])
            return
        link = targets.write(free[0], r["title"], html)
        results["targets_used"].append(free[0])
        check = verify.verify_article(free[0], note, before, client=targets.client, swaps=swaps)
        r.update(outcome="draft_written", target_id=free[0], target_link=link)
    else:
        check = verify.verify_article(r["article_id"], note, before, client=ticket_run._LocalHTML(html), swaps=swaps)
        r.update(outcome="draft_saved")
    r["warnings"] = check.warnings
    r["at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    log(f"  [{r['n']}] {r['title']}: draft updated ({r['outcome']})")

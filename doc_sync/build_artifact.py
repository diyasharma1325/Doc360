"""Build the Jira-style artifact page for a ticket run, as the I2P backtest
does for its runs (i2p-backtest/scripts/build_artifact.py).

    python3 doc_sync/build_artifact.py <run> --title "Display Names Doc Sync"

Reads everything the run recorded (ticket.json, out/jira_log.json, the
comments, change_note.json, plan.json, approved.json, results.json and the
before/after HTML) and writes runs/<run>/artifact.html from
templates/artifact.html: the ticket header, a details sidebar, the activity
timeline (every status move, comment, the extracted change note and the
approval, in order), the proposed edits as word-level diffs, and a footnote
on how the run differs from production. Comments are reproduced as recorded,
with three exceptions so nothing shows twice: the phase 2 / screenshots
comments' per-screenshot lists become a pointer to Proposed edits (where each
screenshot is shown with the same instructions), a 'UI facts confirmed' reply
drops its copy of the list, and a writer's UI facts that a later set replaced
collapse to one line. The comment files are unchanged. The page is static:
publish it with the Artifact tool.

Works on a run at any stage; whatever hasn't happened yet is left out.
"""
import argparse
import base64
import difflib
import io
import html
import json
import re
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

import ticket

THIS_DIR = Path(__file__).resolve().parent
TEMPLATE = THIS_DIR / "templates" / "artifact.html"
AGENT = "Doc Sync Agent"
AGENT_INITIALS = "DS"

esc = html.escape


# --- Markdown (the small subset the recorded comments use) ----------------------

def _inline(text):
    """Escape, then `code`, [text](url) and **bold**."""
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append(f"<code>{esc(part[1:-1])}</code>")
            continue
        s = esc(part)
        s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                   lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        out.append(s)
    return "".join(out)


def _cells(row):
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", row)]


LONG_TABLE_ROWS = 15


def render_markdown(text):
    """Paragraphs, bullet lists and pipe tables, with inline formatting."""
    blocks = re.split(r"\n\s*\n", (text or "").strip())
    out = []
    for block in blocks:
        lines = [l for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        if all(l.lstrip().startswith("|") for l in lines) and len(lines) >= 2:
            head, body = _cells(lines[0]), [_cells(l) for l in lines[2:]]
            t = ["<div class=\"tablewrap\"><table><thead><tr>"]
            t += [f"<th>{_inline(c)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for r in body:
                t.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            table = "".join(t)
            if len(body) > LONG_TABLE_ROWS:  # e.g. a 100-row plan: collapsed so the rail stays readable
                table = (f'<details class="longtable"><summary>Show all {len(body)} rows</summary>'
                         f'{table}</details>')
            out.append(table)
        elif all(l.lstrip().startswith("- ") for l in lines):
            out.append("<ul>" + "".join(f"<li>{_inline(l.lstrip()[2:])}</li>" for l in lines) + "</ul>")
        else:
            out.append("<p>" + "<br>".join(_inline(l) for l in lines) + "</p>")
    return "\n".join(out)


# --- diffs ---------------------------------------------------------------------

def _text_lines(html_content):
    text = BeautifulSoup(html_content or "", "html.parser").get_text("\n")
    return [" ".join(l.split()) for l in text.splitlines() if l.strip()]


def _word_diff(a, b):
    aw, bw = a.split(" "), b.split(" ")
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, aw, bw, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(esc(" ".join(aw[i1:i2])))
        else:
            if i2 > i1:
                out.append(f"<del>{esc(' '.join(aw[i1:i2]))}</del>")
            if j2 > j1:
                out.append(f"<ins>{esc(' '.join(bw[j1:j2]))}</ins>")
    return " ".join(out)


def render_diff(before_html, after_html, context=1):
    """The article's visible text, before vs after: changed lines word by
    word, one line of context, unchanged stretches collapsed. Returns
    (html, changed_line_count)."""
    a, b = _text_lines(before_html), _text_lines(after_html)
    rows, changed = [], 0
    ops = difflib.SequenceMatcher(None, a, b, autojunk=False).get_grouped_opcodes(context)
    for gi, group in enumerate(ops):
        if gi:
            rows.append('<div class="ln gap">⋯</div>')
        for op, i1, i2, j1, j2 in group:
            if op == "equal":
                rows += [f'<div class="ln ctx">{esc(l)}</div>' for l in a[i1:i2]]
            elif op == "replace" and (i2 - i1) == (j2 - j1):
                for x, y in zip(a[i1:i2], b[j1:j2]):
                    rows.append(f'<div class="ln"><span class="sign">~</span>{_word_diff(x, y)}</div>')
                    changed += 1
            else:
                rows += [f'<div class="ln del-line"><span class="sign">−</span><del>{esc(l)}</del></div>'
                         for l in a[i1:i2]]
                rows += [f'<div class="ln ins-line"><span class="sign">+</span><ins>{esc(l)}</ins></div>'
                         for l in b[j1:j2]]
                changed += (i2 - i1) + (j2 - j1)
    if not rows:
        return '<div class="ln ctx">No visible text changed (markup only).</div>', 0
    return "\n".join(rows), changed


# --- page pieces ---------------------------------------------------------------

def _when(ts):
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%-d %b %H:%M")
    except (TypeError, ValueError):
        return ts or ""


def _initials(name):
    return "".join(w[0] for w in (name or "W").split()[:2]).upper()


def _who(actor, writer, when, extra=""):
    if actor == "writer":
        return (f'<span class="avatar human" aria-hidden="true">{esc(_initials(writer))}</span>'
                f'<div class="who"><b>{esc(writer)}</b><span class="tag human">Writer</span>'
                f'<time>{esc(when)}</time>{extra}</div>')
    return (f'<span class="avatar agent" aria-hidden="true">{AGENT_INITIALS}</span>'
            f'<div class="who"><b>{AGENT}</b><span class="tag agent">Agent</span>'
            f'<time>{esc(when)}</time>{extra}</div>')


STEP_NOTES = {
    (ticket.TO_DO, ticket.IN_DRAFT): "Moving the ticket to In Draft starts intake: the agent reads the summary, "
                                     "description and attachments and extracts the change note, including the "
                                     "product lines the writer named.",
    (ticket.IN_DRAFT, ticket.TO_DO): "Bounced back to To Do: the ticket couldn't be started as written.",
    (ticket.IN_DRAFT, ticket.PEER_REVIEW): "Phase 1 finished: the candidate plan is posted for the writer to "
                                           "approve or revise.",
    (ticket.PEER_REVIEW, ticket.FOR_REVIEW): "Moving the ticket to For review is the approval. Phase 2 reads "
                                             "each approved article against the change and drafts the edits.",
}


def _product_lines_source_row(ev):
    """Where intake's product lines came from. Older runs logged only a
    `product_lines_quote` (the words that named them)."""
    source = ev.get("product_lines_source")
    basis = ev.get("product_lines_basis") or ev.get("product_lines_quote") or ""
    if source == "ticket":
        return ("Source", "Set on the ticket")
    if source == "predicted":
        return ("Source", "Predicted, for the writer to confirm" + (f": {esc(basis)}" if basis else ""))
    return ("Named as", f"“{esc(basis)}”" if basis else "—")


def _intake_card(ev, note):
    rows = [("Feature", esc(note.get("feature_area", ""))),
            ("Product lines", " · ".join(esc(p) for p in ev.get("product_lines") or [])),
            _product_lines_source_row(ev),
            ("Before", esc(note.get("old", ""))),
            ("After", esc(note.get("new", "")))]
    if note.get("affected_content_types"):
        rows.append(("Affects", esc(", ".join(note["affected_content_types"]))))
    if note.get("unaffected_content_types"):
        rows.append(("Doesn't affect", esc(", ".join(note["unaffected_content_types"]))))
    read = ev.get("attachments_read") or []
    rows.append(("Read", esc(", ".join(read)) if read else "the summary and description only"))
    body = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    return f'<div class="comment agent note-card"><dl>{body}</dl></div>'


# Blocks of the phase 2 / screenshots comment that list each screenshot to
# act on. The page shows every one of them, with its instructions, under
# Proposed edits, so in the activity rail they become one pointer line.
_SHOT_LIST_HEADS = ("**Replaced from another article**", "**To retake.**", "**To check in the product**")
_SHOT_LIST_END = "When the retakes are saved"
_SHOT_POINTER = ("Each screenshot to retake, check or confirm is shown under **Proposed edits** below, "
                 "with its instructions.")


def _without_shot_lists(body):
    """The comment without its per-screenshot lists, plus one pointer line
    where they were. The comment file itself is unchanged."""
    out, skipping, pointed = [], False, False
    for line in body.split("\n"):
        if line.startswith(_SHOT_LIST_HEADS):
            skipping = True
            if not pointed:
                out += [_SHOT_POINTER, ""]
                pointed = True
            continue
        if skipping:
            if line.startswith(_SHOT_LIST_END):
                skipping = False
                continue
            if line.startswith("**"):  # the next section of the comment
                skipping = False
            else:
                continue
        out.append(line)
    return "\n".join(out)


def _fact_list_dropped(body):
    """A 'UI facts confirmed' comment without its copy of the list (the
    writer's comment just above it has the list)."""
    head = body.split("\n", 1)[0].rstrip(":")
    if head.endswith("against these UI facts"):
        head = head[: -len("these UI facts")] + "the UI facts above."
    return head


def build_activity(rd, tk, log, note):
    writer = tk.get("assignee") or "Writer"
    items = []
    # Only the writer's LATEST UI facts are shown in full: an earlier set,
    # and its confirmation, collapse to one line.
    facts_events = [i for i, ev in enumerate(log)
                    if ev["kind"] == "comment" and ev.get("label") == "UI facts" and ev.get("actor") == "writer"]
    latest_facts = facts_events[-1] if facts_events else None
    for i, ev in enumerate(log):
        kind, when = ev["kind"], _when(ev.get("t"))
        if kind == "created":
            items.append(_who("writer", writer, when, "<span>created the ticket</span>")
                         + '<div class="move"><span class="status">To Do</span></div>')
        elif kind == "edited":
            items.append(_who("writer", writer, when,
                              f"<span>edited the ticket ({esc(', '.join(ev.get('fields') or []))})</span>"))
        elif kind == "transition":
            frm, to = ev.get("frm"), ev.get("to")
            watched = lambda s: "status watched" if s in (ticket.IN_DRAFT, ticket.FOR_REVIEW) else "status"
            prev = log[i - 1] if i else {}
            verb = "approved the plan:" if prev.get("kind") == "approval" else "moved the ticket"
            approval = ""
            if prev.get("kind") == "approval":
                nums = ", ".join(str(n) for n in prev.get("numbers") or [])
                approval = (f'<p class="step-note">Approved {len(prev.get("numbers") or [])} article(s) from '
                            f'plan v{prev.get("plan_version")}: #{esc(nums)}.</p>')
            note_text = STEP_NOTES.get((frm, to))
            items.append(
                _who(ev.get("actor", "agent"), writer, when)
                + f'<div class="move">{verb} <span class="{watched(frm)}">{esc(frm or "")}</span>'
                  f'<span aria-hidden="true">→</span><span class="{watched(to)}">{esc(to or "")}</span></div>'
                + approval
                + (f'<p class="step-note">{esc(note_text)}</p>' if note_text else ""))
        elif kind == "comment":
            body = (rd / "out" / ev["file"]).read_text()
            actor, label = ev.get("actor", "agent"), ev.get("label", "")
            superseded = latest_facts is not None and i < latest_facts
            if label == "UI facts" and actor == "writer" and superseded:
                items.append(_who(actor, writer, when, "<span>set the UI facts</span>")
                             + '<p class="step-note">Replaced by a later version, below.</p>')
                continue
            if label == "UI facts confirmed":
                if superseded:
                    continue
                body = _fact_list_dropped(body)
            elif label in ("drafts ready", "screenshots updated"):
                body = _without_shot_lists(body)
            items.append(_who(actor, writer, when, f"<span>commented · {esc(label)}</span>")
                         + f'<div class="comment {"human" if actor == "writer" else "agent"}">'
                           f'{render_markdown(body)}</div>')
        elif kind == "intake" and note:
            items.append(_who("agent", writer, when, "<span>extracted the change note</span>")
                         + _intake_card(ev, note))
    return "\n".join(f'          <li class="ev">{x}</li>' for x in items)


SHOT_LABELS = {"retake": "To retake", "unsure": "To check", "reused": "Replaced from another article",
               "replaced": "Replaced with your retake", "kept": "Kept as it is"}
THUMB_SIDE = 420


def _thumb(path):
    """A small JPEG of a local image as a data: URI, so the page carries its
    own screenshots (Document360's image links expire within minutes)."""
    try:
        from PIL import Image

        im = Image.open(path).convert("RGB")
        im.thumbnail((THUMB_SIDE, THUMB_SIDE))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=78)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


def _figure(path, caption):
    uri = _thumb(path) if path and Path(path).exists() else ""
    if not uri:
        return f'<figure><div class="empty">{esc(caption)}</div></figure>'
    return f'<figure><img src="{uri}" alt="{esc(caption)}"><figcaption>{esc(caption)}</figcaption></figure>'


def build_screenshots(rd, r):
    """The screenshot rows for one article: every image that isn't simply
    fine, old next to new."""
    imgs = r.get("images")
    if not imgs:
        if r.get("images_error"):
            return f'<p class="why">⚠ The screenshot check failed: {esc(r["images_error"][:200])}</p>'
        return ""
    out_dir = rd / "out"
    items = [i for i in imgs["items"] if i["status"] != "fine"]
    fine = sum(1 for i in imgs["items"] if i["status"] == "fine")
    rows = []
    for i in items:
        old = _figure(out_dir / i["file"] if i.get("file") else None, f"Image {i['n']} now")
        if i["status"] == "reused":
            u = i["reuse"]
            new = _figure(out_dir / u["file"] if u.get("file") else None,
                          f"Image {u.get('image_n') or '?'} from {u.get('title') or 'another article'}")
            what = (u.get("reason") or "") + f" To undo it, reply reject {r['n']}:{i['n']}."
        elif i["status"] == "replaced":
            new = _figure(rd / i["new_file"] if i.get("new_file") else None, "Your retake")
            what = i.get("retake") or i.get("reason") or ""
        elif i["status"] == "retake":
            ref = i.get("reference")
            new = (_figure(out_dir / ref["file"] if ref.get("file") else None,
                           f"Close match: image {ref.get('image_n') or '?'} from {ref.get('title')}")
                   if ref else f'<figure><div class="empty">Save the retake as screenshots/{r["n"]}/'
                               f'{i["n"]:03d}.png</div></figure>')
            what = (i.get("retake") or i.get("reason") or "")
            what += f" Save it as screenshots/{r['n']}/{i['n']:03d}.png."
            if i.get("retake_problem"):
                what += f" ⚠ Last attempt: {i['retake_problem']}"
        else:
            new = '<figure><div class="empty">Check this in the product</div></figure>'
            what = ((i.get("reason") or "") + f" If it's fine as it is, reply fine {r['n']}:{i['n']}; if not, "
                    f"save a retake as screenshots/{r['n']}/{i['n']:03d}.png.")
        label = SHOT_LABELS.get(i["status"], i["status"])
        rows.append(f'<div class="shot">{old}{new}<p class="what"><span class="outcome {esc(i["status"])}">'
                    f'{esc(label)}</span> {esc(what)}</p></div>')
    head = f"Screenshots: {imgs['reviewed']} checked, {fine} fine"
    if not rows:
        return f'<p class="why">{esc(head)}.</p>'
    return (f'<details open><summary>{esc(head)}, {len(rows)} need attention</summary>'
            f'<div class="shots">{"".join(rows)}</div></details>')


def build_edits(rd, results, plan):
    rows = sorted((r for r in results.get("articles", {}).values()
                   if r.get("after") or r.get("images") or r.get("images_error")), key=lambda r: r["n"])
    if not rows:
        return ""
    labels = {"merge_conflict": ("Needs a manual merge", "merge"), "draft_written": ("Draft written", "written"),
              "draft_saved": ("Draft saved locally", "saved"), "no_edit": ("No edit needed", "saved"),
              "screenshots_pending": ("Screenshots to retake", "merge")}
    out = ['      <section>', '        <p class="label">Proposed edits</p>']
    for r in rows:
        if r.get("after"):
            before = (rd / "out" / r["before"]).read_text() if r.get("before") else ""
            after = (rd / "out" / r["after"]).read_text()
            diff, changed = render_diff(before, after)
        else:
            diff, changed = "", 0
        label, cls = labels.get(r["outcome"], (r["outcome"], "saved"))
        where = ""
        if r.get("target_link"):
            where = f' · <a href="{esc(r["target_link"])}" target="_blank" rel="noopener">open the Archived draft</a>'
        conf = f'<span class="chip">{esc(r["confidence"])} confidence</span>' if r.get("confidence") else ""
        text = ""
        if diff:
            text = ('<details open><summary>Before → after, visible text only</summary>\n'
                    f'            <div class="diff">\n{diff}\n            </div>\n          </details>')
        warn = ""
        if r.get("warnings"):
            warn = f'<p class="why">⚠ {esc("; ".join(r["warnings"]))}</p>'
        out.append(f"""        <article class="edit">
          <div class="head"><h2>#{r['n']} {esc(r['title'])}</h2><span class="outcome {cls}">{esc(label)}</span></div>
          <div class="chips"><span class="chip">{esc(r.get('workspace') or '')}</span>{conf}<span class="chip">{changed} line(s) changed</span></div>
          <p class="why">{esc(r.get('rationale') or '')}{where}</p>
          {warn}
          {text}
          {build_screenshots(rd, r)}
        </article>""")
    out.append("      </section>")
    return "\n".join(out)


def build_details(tk, note, plan, approved, results):
    rows = [("Work type", "Doc Sync"),
            ("Status", f'<span class="status watched">{esc(tk.get("status", ""))}</span>'),
            ("Assignee", esc(tk.get("assignee") or "Writer"))]
    if note:
        rows.append(("Product lines", '<div class="chips">' + "".join(
            f'<span class="chip">{esc(p)}</span>' for p in note.get("product_lines") or []) + "</div>"))
        rows.append(("Feature", f"<code>{esc(note.get('feature_area', ''))}</code>"))
    if plan:
        rows.append(("Discovery", f"{esc(plan['discovery'])} search, {plan['scanned']:,} article(s) scanned"))
        rows.append(("Plan", f"v{plan['version']}, {len(plan['candidates'])} candidate(s)"))
    if approved:
        rows.append(("Approved", f"{len(approved['articles'])} article(s)"))
    arts = list((results or {}).get("articles", {}).values())
    if arts:
        names = {"draft_written": "draft written", "draft_saved": "draft saved", "no_edit": "no edit needed",
                 "screenshots_pending": "screenshots to retake", "merge_conflict": "manual merge",
                 "failed": "failed"}
        counts = {k: sum(1 for r in arts if r["outcome"] == k) for k in names}
        rows.append(("Result", ", ".join(f"{v} {names[k]}" for k, v in counts.items() if v)))
    path = [ticket.TO_DO, ticket.IN_DRAFT, ticket.PEER_REVIEW, ticket.FOR_REVIEW]
    strip = '<span aria-hidden="true">→</span>'.join(
        f'<span class="here">{esc(s)}</span>' if s == tk.get("status") else f"<span>{esc(s)}</span>" for s in path)
    rows.append(("Status path", f'<span class="flowstrip">{strip}</span>'))
    return "\n".join(f"        <div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows)


def build_attachments(rd, tk):
    names = tk.get("attachments") or []
    if not names:
        return '<p class="desc">None.</p>'
    import pdf_text
    tiles = []
    for n in names:
        p = rd / "attachments" / n
        size = p.stat().st_size if p.exists() else 0
        info = pdf_text.read_attachment(p)
        meta = f"{size / 1_000_000:.1f} MB" if size >= 1_000_000 else f"{size / 1000:.0f} KB"
        meta += f" · {info['pages']} page(s), read" if not info["problem"] else f" · not read: {info['problem']}"
        tiles.append(f'<div class="file"><span class="ext">PDF</span><div><div class="name">{esc(n)}</div>'
                     f'<div class="meta">{esc(meta)}</div></div></div>')
    return '<div class="files">' + "".join(tiles) + "</div>"


def build_footnote(results, plan):
    notes = ["This is a simulated Jira ticket. No real Jira was used: every status move and comment above was "
             "recorded locally by the pipeline and is reproduced exactly as recorded."]
    arts = list((results or {}).get("articles", {}).values())
    if any(r["outcome"] == "draft_written" for r in arts):
        notes.append("Drafts were written into scratch articles in Document360's Archived workspace, which is "
                     "where the draft links point. No live article was written or published.")
    elif arts:
        notes.append("Nothing was written to Document360. Live articles were only read; the proposed edits are "
                     "saved as HTML in the run folder.")
    notes.append("Model calls ran through Claude Code (claude -p) on the writer's login, not an API key.")
    return "\n".join(f"    <p>{esc(n)}</p>" for n in notes)


def build(run, title):
    rd = ticket.run_dir(run)
    tk = ticket.load_ticket(rd)
    log = ticket.load_log(rd)
    load = lambda name: json.loads((rd / name).read_text()) if (rd / name).exists() else None
    note, plan, approved, results = load("change_note.json"), load("plan.json"), load("approved.json"), load("results.json")

    try:
        date = datetime.strptime(tk.get("created_at", ""), "%Y-%m-%d %H:%M:%S").strftime("%-d %b %Y")
    except ValueError:
        date = ""
    fill = {
        "PAGE_TITLE": esc(title), "KEY": esc(tk["key"]), "DATE": esc(date),
        "SUMMARY": esc(tk["summary"]), "DESCRIPTION": esc(tk.get("description") or ""),
        "ATTACH_COUNT": str(len(tk.get("attachments") or [])), "ATTACHMENTS": build_attachments(rd, tk),
        "ACTIVITY": build_activity(rd, tk, log, note),
        "EDITS": build_edits(rd, results or {}, plan),
        "DETAILS": build_details(tk, note, plan, approved, results),
        "FOOTNOTE": build_footnote(results, plan),
    }
    page = TEMPLATE.read_text()
    for k, v in fill.items():
        page = page.replace("{{" + k + "}}", v)
    left = re.search(r"\{\{[A-Z_]+\}\}", page)
    if left:
        raise SystemExit(f"Unfilled placeholder: {left.group(0)}")
    dest = rd / "artifact.html"
    dest.write_text(page)
    return dest


def main():
    parser = argparse.ArgumentParser(description="Build the Jira-style artifact page for a ticket run.")
    parser.add_argument("run", help="Run name (under doc_sync/runs/) or path")
    parser.add_argument("--title", required=True, help="2-4 word page name, e.g. 'Display Names Doc Sync'")
    args = parser.parse_args()
    print(build(args.run, args.title))


if __name__ == "__main__":
    main()

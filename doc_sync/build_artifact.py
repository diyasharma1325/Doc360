"""Build the Jira-style artifact page for a ticket run, as the I2P backtest
does for its runs (i2p-backtest/scripts/build_artifact.py).

    python3 doc_sync/build_artifact.py <run> --title "Display Names Doc Sync"

Reads everything the run recorded (ticket.json, out/jira_log.json, the
comments, change_note.json, plan.json, approved.json, results.json and the
before/after HTML) and writes runs/<run>/artifact.html from
templates/artifact.html: the ticket header, a details sidebar, the activity
timeline (every status move, comment, the extracted change note and the
approval, in order), the proposed edits as word-level diffs, and a footnote
on how the run differs from production. Comments are reproduced exactly as
recorded. The page is static: publish it with the Artifact tool.

Works on a run at any stage; whatever hasn't happened yet is left out.
"""
import argparse
import difflib
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
            out.append("".join(t))
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


def build_activity(rd, tk, log, note):
    writer = tk.get("assignee") or "Writer"
    items = []
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
            actor = ev.get("actor", "agent")
            items.append(_who(actor, writer, when, f"<span>commented · {esc(ev.get('label', ''))}</span>")
                         + f'<div class="comment {"human" if actor == "writer" else "agent"}">'
                           f'{render_markdown(body)}</div>')
        elif kind == "intake" and note:
            items.append(_who("agent", writer, when, "<span>extracted the change note</span>")
                         + _intake_card(ev, note))
    return "\n".join(f'          <li class="ev">{x}</li>' for x in items)


def build_edits(rd, results, plan):
    rows = sorted((r for r in results.get("articles", {}).values() if r.get("after")), key=lambda r: r["n"])
    if not rows:
        return ""
    labels = {"merge_conflict": ("Needs a manual merge", "merge"), "draft_written": ("Draft written", "written"),
              "draft_saved": ("Draft saved locally", "saved")}
    out = ['      <section>', '        <p class="label">Proposed edits</p>']
    for r in rows:
        before = (rd / "out" / r["before"]).read_text() if r.get("before") else ""
        after = (rd / "out" / r["after"]).read_text()
        diff, changed = render_diff(before, after)
        label, cls = labels.get(r["outcome"], (r["outcome"], "saved"))
        where = ""
        if r.get("target_link"):
            where = f' · <a href="{esc(r["target_link"])}" target="_blank" rel="noopener">open the Archived draft</a>'
        warn = ""
        if r.get("warnings"):
            warn = f'<p class="why">⚠ {esc("; ".join(r["warnings"]))}</p>'
        out.append(f"""        <article class="edit">
          <div class="head"><h2>#{r['n']} {esc(r['title'])}</h2><span class="outcome {cls}">{esc(label)}</span></div>
          <div class="chips"><span class="chip">{esc(r.get('workspace') or '')}</span><span class="chip">{esc(r.get('confidence') or '?')} confidence</span><span class="chip">{changed} line(s) changed</span></div>
          <p class="why">{esc(r.get('rationale') or '')}{where}</p>
          {warn}
          <details open><summary>Before → after, visible text only</summary>
            <div class="diff">
{diff}
            </div>
          </details>
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
                 "merge_conflict": "manual merge", "failed": "failed"}
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

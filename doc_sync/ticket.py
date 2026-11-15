"""The simulated Jira ticket that drives a doc-sync run, and the local
recorder for everything that would happen on it.

There is no real Jira here. A ticket is a summary, a free-text description,
optional product lines, optional PDF attachments and an assignee, written by the writer and stored
in its own run folder. Every status move and comment the pipeline would
make on a real ticket is recorded locally instead, in the same layout as
the I2P backtest (i2p-agent-master/.claude/skills/i2p-backtest), so the
Jira-style artifact can be built from it:

    doc_sync/runs/<name>/
        ticket.json          key, summary, description, assignee, attachments, status
        attachments/         copies of the attached PDFs
        change_note.json     what intake extracted (ticket_intake.py)
        out/jira_log.json    every event, in order: transitions, comments, ...
        out/comment-NN.txt   each comment body, Markdown

Run folders are git-ignored: they hold copies of PDFs and, later, live
article content.

The four statuses are the I2P board's, in the same order:
To Do -> In Draft -> Peer review -> For review.

    python3 doc_sync/ticket.py new <name> --summary "..." --description-file desc.txt \
        [--product-lines "DAP for Web, DAP for Desktop"] [--attach prd.pdf ...]
    python3 doc_sync/ticket.py update <name> --description-file desc.txt   # fix a bounced ticket

PRODUCT LINES (2026-11-15). The ticket creator MAY set them as a field
(`--product-lines`, like a Jira field). When set, intake uses exactly those
and predicts nothing. When not set, intake takes the ones the summary or
description names, or else predicts them for the writer to confirm
(ticket_intake.py).
    python3 doc_sync/ticket.py show <name>
"""
import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))  # workspaces.py
import workspaces

RUNS_DIR = Path(__file__).resolve().parent / "runs"

TO_DO = "To Do"
IN_DRAFT = "In Draft"
PEER_REVIEW = "Peer review"
FOR_REVIEW = "For review"
STATUSES = (TO_DO, IN_DRAFT, PEER_REVIEW, FOR_REVIEW)

KEY_PREFIX = "WSC-9000"  # simulated keys, WSC-900001 upward, as in the I2P backtest
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")


def run_dir(run):
    """A run's folder from its name (under doc_sync/runs/) or a path."""
    p = Path(run).expanduser()
    if p.is_absolute() or p.exists():
        return p
    return RUNS_DIR / str(run)


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _next_key():
    used = set()
    for f in RUNS_DIR.glob("*/ticket.json"):
        try:
            used.add(json.loads(f.read_text()).get("key"))
        except (OSError, ValueError):
            continue
    n = 1
    while f"{KEY_PREFIX}{n:02d}" in used:
        n += 1
    return f"{KEY_PREFIX}{n:02d}"


def check_product_lines(names):
    """The ticket creator's product lines in the allow-list's spelling,
    de-duplicated. Raises ValueError naming any that isn't one of the six
    live workspaces, so a typo is caught when the ticket is made."""
    out, bad = [], []
    for name in names or []:
        version_id = workspaces.id_for_name(name)
        if not version_id:
            bad.append(name)
        elif workspaces.LIVE_WORKSPACES[version_id] not in out:
            out.append(workspaces.LIVE_WORKSPACES[version_id])
    if bad:
        raise ValueError(f"Not a live product line: {', '.join(repr(b) for b in bad)}. "
                         f"The product lines are: {', '.join(workspaces.names())}.")
    return out


def new_run(name, summary, description, attachments=(), assignee="Writer", product_lines=None):
    """Create runs/<name>/ with its ticket.json and copies of the attachments.
    Refuses a name that exists or isn't a short lowercase slug. Returns the
    run folder. `product_lines` is the optional field set by the ticket's
    creator (check_product_lines)."""
    if not _NAME_RE.match(name or ""):
        raise ValueError(f"Run name {name!r} must be a lowercase slug, e.g. 'dap-display-names'.")
    rd = RUNS_DIR / name
    if rd.exists():
        raise FileExistsError(f"Run {name!r} already exists at {rd} — pick another name.")
    if not (summary or "").strip():
        raise ValueError("A ticket needs a summary.")
    product_lines = check_product_lines(product_lines)
    sources = [Path(a).expanduser() for a in attachments or ()]
    for src in sources:
        if not src.is_file():
            raise FileNotFoundError(f"Attachment not found: {src}")
        if src.suffix.lower() != ".pdf":
            raise ValueError(f"Attachment {src.name} is not a PDF; only PDF attachments are supported.")

    (rd / "attachments").mkdir(parents=True)
    (rd / "out").mkdir()
    names = []
    for src in sources:
        shutil.copy2(src, rd / "attachments" / src.name)
        names.append(src.name)
    ticket = {
        "key": _next_key(),
        "summary": summary.strip(),
        "description": (description or "").strip(),
        "assignee": (assignee or "Writer").strip(),
        "product_lines": product_lines,
        "attachments": names,
        "status": TO_DO,
        "created_at": _now(),
    }
    (rd / "ticket.json").write_text(json.dumps(ticket, indent=2))
    record_event(rd, "created", status=TO_DO)
    return rd


def update_ticket(run, summary=None, description=None, attachments=(), product_lines=None):
    """Edit a ticket the way a writer fixes one that was bounced: new
    summary/description, more attachments. Only in To Do, so a ticket the
    pipeline is already working from never changes underneath it."""
    rd = run_dir(run)
    tk = load_ticket(rd)
    if tk.get("status") != TO_DO:
        raise ValueError(f"{tk['key']} is in {tk.get('status')!r}; a ticket can only be edited in {TO_DO!r}.")
    changed = []
    if summary is not None and summary.strip():
        tk["summary"] = summary.strip()
        changed.append("summary")
    if description is not None:
        tk["description"] = description.strip()
        changed.append("description")
    if product_lines is not None:
        tk["product_lines"] = check_product_lines(product_lines)
        changed.append("product lines")
    for a in attachments or ():
        src = Path(a).expanduser()
        if not src.is_file() or src.suffix.lower() != ".pdf":
            raise ValueError(f"Attachment {src} is not an existing PDF.")
        shutil.copy2(src, rd / "attachments" / src.name)
        if src.name not in tk["attachments"]:
            tk["attachments"].append(src.name)
        changed.append(f"attachment {src.name}")
    save_ticket(rd, tk)
    if changed:
        record_event(rd, "edited", actor="writer", fields=changed)
    return tk


def load_ticket(run):
    path = run_dir(run) / "ticket.json"
    if not path.exists():
        raise FileNotFoundError(f"No ticket.json in {path.parent} — create the run with: ticket.py new")
    return json.loads(path.read_text())


def save_ticket(run, ticket):
    (run_dir(run) / "ticket.json").write_text(json.dumps(ticket, indent=2))


def attachment_paths(run):
    rd = run_dir(run)
    return [rd / "attachments" / n for n in load_ticket(rd).get("attachments", [])]


def load_log(run):
    path = run_dir(run) / "out" / "jira_log.json"
    return json.loads(path.read_text()) if path.exists() else []


def record_event(run, kind, **fields):
    """Append one event to out/jira_log.json and return it."""
    out = run_dir(run) / "out"
    out.mkdir(parents=True, exist_ok=True)
    log = load_log(run)
    event = {"t": _now(), "kind": kind, **fields}
    log.append(event)
    (out / "jira_log.json").write_text(json.dumps(log, indent=1))
    return event


def record_transition(run, to, actor="agent"):
    """Move the ticket to status `to` and record it. `actor` is "writer"
    (a move the writer makes) or "agent" (one the pipeline makes)."""
    if to not in STATUSES:
        raise ValueError(f"Unknown status {to!r}; statuses are {STATUSES}")
    ticket = load_ticket(run)
    frm = ticket.get("status")
    ticket["status"] = to
    save_ticket(run, ticket)
    print(f"    [ticket {ticket['key']}] {actor} moved {frm} -> {to}", flush=True)
    return record_event(run, "transition", actor=actor, frm=frm, to=to)


def record_comment(run, body, label, actor="agent"):
    """Save a comment as out/comment-NN.txt and record it. `label` says what
    it is ("candidate plan", "intake bounced", ...), for the artifact."""
    out = run_dir(run) / "out"
    out.mkdir(parents=True, exist_ok=True)
    n = len(list(out.glob("comment-*.txt"))) + 1
    path = out / f"comment-{n:02d}.txt"
    path.write_text(body)
    print(f"    [ticket {load_ticket(run)['key']}] {actor} commented ({label}) -> {path}", flush=True)
    return record_event(run, "comment", actor=actor, label=label, file=path.name)


def main():
    parser = argparse.ArgumentParser(description="Create or inspect a simulated Jira ticket for a doc-sync run.")
    sub = parser.add_subparsers(dest="command", required=True)

    new_p = sub.add_parser("new", help="Create a run folder with its ticket")
    new_p.add_argument("name", help="Run name, a lowercase slug, e.g. dap-display-names")
    new_p.add_argument("--summary", required=True, help="The ticket's summary (Jira title), word for word")
    desc = new_p.add_mutually_exclusive_group()
    desc.add_argument("--description", default="", help="The ticket's description, word for word")
    desc.add_argument("--description-file", help="Read the description from this file instead")
    new_p.add_argument("--product-lines", default=None,
                       help="Optional: the product lines this change ships in, comma-separated (e.g. 'DAP "
                            "for Web, DAP for Desktop'). Set, they are used as is and none are predicted.")
    new_p.add_argument("--attach", action="append", default=[], help="A PDF attachment (repeatable)")
    new_p.add_argument("--assignee", default="Writer", help="The writer's name, shown on the artifact")

    upd_p = sub.add_parser("update", help="Fix a ticket in To Do (e.g. after a bounce)")
    upd_p.add_argument("name")
    upd_p.add_argument("--summary")
    upd_desc = upd_p.add_mutually_exclusive_group()
    upd_desc.add_argument("--description")
    upd_desc.add_argument("--description-file")
    upd_p.add_argument("--product-lines", default=None,
                       help="Set the product lines field, comma-separated; pass \"\" to clear it")
    upd_p.add_argument("--attach", action="append", default=[], help="Add a PDF attachment (repeatable)")

    show_p = sub.add_parser("show", help="Print a run's ticket and its recorded activity")
    show_p.add_argument("name")

    args = parser.parse_args()
    if args.command == "new":
        description = Path(args.description_file).read_text() if args.description_file else args.description
        rd = new_run(args.name, args.summary, description, args.attach, args.assignee,
                     _split(args.product_lines))
        print(f"Created {load_ticket(rd)['key']} in {rd}")
    elif args.command == "update":
        description = Path(args.description_file).read_text() if args.description_file else args.description
        lines = None if args.product_lines is None else _split(args.product_lines)
        tk = update_ticket(args.name, args.summary, description, args.attach, lines)
        print(f"Updated {tk['key']}")
    else:
        print(json.dumps(load_ticket(args.name), indent=2))
        for e in load_log(args.name):
            print(" ", json.dumps(e))


def _split(text):
    return [n.strip() for n in (text or "").split(",") if n.strip()]


if __name__ == "__main__":
    main()

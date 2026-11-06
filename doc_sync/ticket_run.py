"""Phase 1 of a ticket run, the plan and its approval: the I2P agent's
"IA Plan -> Peer review -> approval" loop, for doc-sync's job of finding
the existing articles a change has made wrong.

    python3 doc_sync/ticket_run.py intake  <run> [--provider gemini]        # To Do -> In Draft
    python3 doc_sync/ticket_run.py phase1  <run> [--discovery both]         # In Draft -> Peer review + plan
    python3 doc_sync/ticket_run.py replan  <run> "<feedback>" [--product-lines ...]
    python3 doc_sync/ticket_run.py approve <run> "1, 3, 5-7" | all          # Peer review -> For review
    python3 doc_sync/ticket_run.py show    <run>

- PHASE 1 runs discovery (kb_search.py) on the change note intake saved,
  within the ticket's product lines, and records the result as a numbered
  "candidate plan" comment, moving the ticket In Draft -> Peer review. The
  plan itself is saved as plan.json. tag_map.json is NOT used: its ids are
  mock fixtures, never live articles.
- RE-PLAN records the writer's feedback as their comment, re-runs triage
  with that feedback and the numbered plan they saw, and records the
  revised plan. The ticket stays in Peer review. `--product-lines` changes
  the scope for this and later re-plans.
- APPROVE takes plan NUMBERS, never typed article ids (a mistyped id once
  sent a test run after an article that doesn't exist), checks every one
  against the plan, saves approved.json and moves the ticket Peer review ->
  For review. After that the plan can't change. Phase 2 (assessment and
  writes) reads approved.json.

Every refusal says why and changes nothing. A failed phase 1 records a
"plan failed" comment and leaves the ticket in In Draft, so it can simply
be run again.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR.parent / "core"))  # d360_client.py / workspaces.py live in ../core

import claude_call
import kb_search
import ticket
from change_note import load_change_note


class StepRefused(RuntimeError):
    """The ticket is not in a state where this step may run."""


# --- run files -----------------------------------------------------------------

def _path(run, name):
    return ticket.run_dir(run) / name


def load_plan(run):
    p = _path(run, "plan.json")
    return json.loads(p.read_text()) if p.exists() else None


def load_approved(run):
    p = _path(run, "approved.json")
    return json.loads(p.read_text()) if p.exists() else None


def _save(run, name, data):
    _path(run, name).write_text(json.dumps(data, indent=2))


def _require_status(tk, status, step):
    if tk.get("status") != status:
        raise StepRefused(f"{tk['key']} is in {tk.get('status')!r}; {step} runs only from {status!r}.")


# --- the plan comment ----------------------------------------------------------

def _cell(text):
    return " ".join(str(text or "").split()).replace("|", "\\|")


def plan_comment(tk, note, plan, revised=False):
    """The candidate plan as a ticket comment (Markdown), numbered so the
    writer approves by number."""
    cands = plan["candidates"]
    scope = ", ".join(plan["scope"])
    both = plan["discovery"] == "both"
    if both:
        how = f"a full-text search plus a title check, {plan['scanned']:,} listing(s) in {scope}"
    else:
        how = f"{plan['discovery']} search of {plan['scanned']:,} article(s) in {scope}"
    head = "Here's the revised candidate plan" if revised else "Here's the candidate plan"
    lines = [f"{head} for **{tk['key']}**.", "", f"**Change:** {note.summary}", ""]
    if not cands:
        lines += [
            f"I found **no articles** that look affected ({how}).",
            "",
            "**Next step:** if you expected some, reply with where to look (other product lines, "
            "other features or wording) and I'll re-plan. There is nothing to approve.",
        ]
        return "\n".join(lines)
    lines += [
        f"These **{len(cands)} article(s)** may be out of date ({how}). Each one you approve gets "
        "a full read against the change, and an edited draft if it needs one.",
        "",
    ]
    if both:
        lines += [
            "**Found by** says which search found each article: **both** (strongest: two separate "
            "methods agree), **index** (its text mentions the change), or **titles** (its title "
            "suggests it, but its text didn't match; worth a quick look).",
            "",
            "| # | Article | Workspace | Found by | Why it may be affected |",
            "|---|---|---|---|---|",
        ]
        for c in cands:
            lines.append(f"| {c['n']} | {_cell(c['title'])} | {_cell(c.get('workspace'))} | "
                         f"{_cell(c.get('found_by'))} | {_cell(c.get('reason'))} |")
    else:
        lines += [
            "| # | Article | Workspace | Why it may be affected |",
            "|---|---|---|---|",
        ]
        for c in cands:
            lines.append(f"| {c['n']} | {_cell(c['title'])} | {_cell(c.get('workspace'))} | {_cell(c.get('reason'))} |")
    lines += [
        "",
        "**Next step:** approve the articles to assess by number, for example `1, 3, 5-7`, or "
        "`all`. That moves the ticket to **For review** and starts the edits. To change the plan "
        "instead, reply with what to change.",
    ]
    return "\n".join(lines)


def _discover(run, note, discovery, provider, scope_override, revision=None):
    """Run discovery and save plan.json. Returns the plan."""
    mode = discovery if (discovery == "titles" or kb_search.index_available()) else "titles"
    scope = kb_search.resolve_scope(note, scope_override, mode)
    _, found, scanned = kb_search.find_candidates_live(
        note, product_lines=scope_override, discovery=discovery, provider=provider, revision=revision,
    )
    previous = load_plan(run)
    plan = {
        "version": (previous or {}).get("version", 0) + 1,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "discovery": mode,
        "provider": provider,
        "scope": scope,
        "scope_override": scope_override,
        "scanned": len(scanned),
        "candidates": [
            {"n": i, "article_id": c["article_id"], "title": c.get("title", ""),
             "workspace": c.get("workspace"), "reason": c.get("reason", ""),
             **({"found_by": c["found_by"]} if c.get("found_by") else {})}
            for i, c in enumerate(found, 1)
        ],
    }
    _save(run, "plan.json", plan)
    return plan


# --- the steps -----------------------------------------------------------------

# Ticket runs search article bodies by default (2026-11-07): on the Display
# Names ticket, index found 12-14 focused candidates for ~$0.13 where titles
# found 101 for ~$0.82. "both" adds a strict title check for thoroughness.
TICKET_DISCOVERY = "index"


def run_phase1(run, discovery=TICKET_DISCOVERY, provider=claude_call.DEFAULT_PROVIDER,
               product_lines=None):
    """In Draft -> Peer review, with the candidate plan as a comment."""
    rd = ticket.run_dir(run)
    tk = ticket.load_ticket(rd)
    _require_status(tk, ticket.IN_DRAFT, "phase 1")
    if not _path(rd, "change_note.json").exists():
        raise StepRefused(f"{tk['key']} has no change note yet: run intake first.")
    if load_plan(rd):
        raise StepRefused(f"{tk['key']} already has a plan; use replan to change it.")
    note = load_change_note(str(_path(rd, "change_note.json")))

    ticket.record_event(rd, "phase1_start", discovery=discovery, provider=provider)
    try:
        plan = _discover(rd, note, discovery, provider, product_lines)
    except Exception as exc:
        ticket.record_comment(rd, (
            "Something went wrong while I was looking for the affected articles, so there is no "
            f"plan yet:\n\n`{type(exc).__name__}: {str(exc)[:300]}`\n\n"
            "The ticket stays in **In Draft**; run phase 1 again to retry."
        ), label="plan failed")
        raise
    ticket.record_transition(rd, ticket.PEER_REVIEW, actor="agent")
    ticket.record_comment(rd, plan_comment(tk, note, plan), label="candidate plan")
    return plan


def run_replan(run, feedback, provider=None, product_lines=None):
    """Re-plan from the writer's feedback; the ticket stays in Peer review."""
    rd = ticket.run_dir(run)
    tk = ticket.load_ticket(rd)
    _require_status(tk, ticket.PEER_REVIEW, "a re-plan")
    plan = load_plan(rd)
    if not plan:
        raise StepRefused(f"{tk['key']} has no plan to revise.")
    if not (feedback or "").strip():
        raise StepRefused("Say what to change: a re-plan needs feedback.")
    note = load_change_note(str(_path(rd, "change_note.json")))

    ticket.record_comment(rd, feedback.strip(), label="revision request", actor="writer")
    scope_override = product_lines or plan.get("scope_override")
    revision = {"feedback": feedback, "previous": plan["candidates"]}
    try:
        new_plan = _discover(rd, note, plan["discovery"], provider or plan["provider"], scope_override, revision)
    except Exception as exc:
        ticket.record_comment(rd, (
            "Something went wrong while I was revising the plan:\n\n"
            f"`{type(exc).__name__}: {str(exc)[:300]}`\n\n"
            "The earlier plan still stands. Ask again to retry."
        ), label="re-plan failed")
        _save(rd, "plan.json", plan)  # _discover may have failed after writing; keep the old plan
        raise
    ticket.record_comment(rd, plan_comment(tk, note, new_plan, revised=True), label="revised candidate plan")
    return new_plan


def parse_selection(text, count):
    """"1, 3, 5-7" or "all" -> sorted plan numbers, each checked to be in
    1..count. Raises ValueError naming what's wrong."""
    text = (text or "").strip().lower()
    if not text:
        raise ValueError("No selection given.")
    if text == "all":
        return list(range(1, count + 1))
    chosen = set()
    for part in re.split(r"[,\s]+", text):
        if not part:
            continue
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", part)
        if not m:
            raise ValueError(f"{part!r} is not a plan number or range (use e.g. 1, 3, 5-7).")
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        if lo > hi:
            raise ValueError(f"Range {part!r} runs backwards.")
        bad = [n for n in range(lo, hi + 1) if not 1 <= n <= count]
        if bad:
            raise ValueError(f"{part!r} is outside the plan, which is numbered 1-{count}.")
        chosen.update(range(lo, hi + 1))
    return sorted(chosen)


def approve(run, selection):
    """Peer review -> For review with the chosen plan numbers."""
    rd = ticket.run_dir(run)
    tk = ticket.load_ticket(rd)
    _require_status(tk, ticket.PEER_REVIEW, "approval")
    plan = load_plan(rd)
    if not plan or not plan["candidates"]:
        raise StepRefused(f"{tk['key']}'s plan has no articles to approve.")
    try:
        numbers = parse_selection(selection, len(plan["candidates"]))
    except ValueError as exc:
        raise StepRefused(str(exc))
    articles = [c for c in plan["candidates"] if c["n"] in numbers]
    _save(rd, "approved.json", {
        "approved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "plan_version": plan["version"],
        "selection": selection,
        "numbers": numbers,
        "articles": articles,
    })
    ticket.record_event(rd, "approval", actor="writer", plan_version=plan["version"], numbers=numbers)
    ticket.record_transition(rd, ticket.FOR_REVIEW, actor="writer")
    return articles


# --- CLI -----------------------------------------------------------------------

def show(run):
    rd = ticket.run_dir(run)
    tk = ticket.load_ticket(rd)
    print(f"{tk['key']}  [{tk['status']}]  {tk['summary']}")
    plan, approved = load_plan(rd), load_approved(rd)
    if plan:
        print(f"Plan v{plan['version']}: {len(plan['candidates'])} candidate(s), {plan['discovery']} "
              f"search in {', '.join(plan['scope'])}")
        picked = set((approved or {}).get("numbers") or [])
        for c in plan["candidates"]:
            mark = "*" if c["n"] in picked else " "
            by = f", {c['found_by']}" if c.get("found_by") else ""
            print(f"  {mark}{c['n']:>3}. {c['title']}  ({c.get('workspace')}{by})")
    if approved:
        print(f"Approved: {approved['numbers']}  (* above)")


def main():
    parser = argparse.ArgumentParser(description="Phase 1 of a ticket run: plan, revise, approve.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("intake", help="To Do -> In Draft: extract the change note (ticket_intake.py)")
    p.add_argument("run")
    p.add_argument("--provider", choices=claude_call.PROVIDERS, default=claude_call.DEFAULT_PROVIDER)

    p = sub.add_parser("phase1", help="In Draft -> Peer review: find candidates, record the plan")
    p.add_argument("run")
    p.add_argument("--discovery", choices=kb_search.DISCOVERY_MODES, default=TICKET_DISCOVERY,
                   help="'index' (default): search article bodies. 'both': index plus a strict title "
                        "check, merged with a Found by column. 'titles': every title only.")
    p.add_argument("--provider", choices=claude_call.PROVIDERS, default=claude_call.DEFAULT_PROVIDER)
    p.add_argument("--product-lines", default=None, help="Override the ticket's product lines (comma-separated)")

    p = sub.add_parser("replan", help="Revise the plan from the writer's feedback")
    p.add_argument("run")
    p.add_argument("feedback")
    p.add_argument("--provider", choices=claude_call.PROVIDERS, default=None)
    p.add_argument("--product-lines", default=None, help="Change the scope (comma-separated)")

    p = sub.add_parser("approve", help="Peer review -> For review: approve plan numbers")
    p.add_argument("run")
    p.add_argument("selection", help='Plan numbers, e.g. "1, 3, 5-7", or "all"')

    p = sub.add_parser("show", help="Print the ticket's status, plan and approval")
    p.add_argument("run")

    args = parser.parse_args()
    try:
        if args.command == "intake":
            import ticket_intake
            outcome = ticket_intake.run_intake(args.run, provider=args.provider)
            if outcome["status"] == "bounced":
                raise SystemExit("Bounced to To Do: " + " ".join(outcome["reasons"]))
            print(f"Product lines: {', '.join(outcome['product_lines'])}")
        elif args.command == "phase1":
            plan = run_phase1(args.run, args.discovery, args.provider,
                              kb_search.parse_product_lines(args.product_lines))
            print(f"Plan v{plan['version']}: {len(plan['candidates'])} candidate(s).")
            show(args.run)
        elif args.command == "replan":
            plan = run_replan(args.run, args.feedback, args.provider,
                              kb_search.parse_product_lines(args.product_lines))
            print(f"Plan v{plan['version']}: {len(plan['candidates'])} candidate(s).")
            show(args.run)
        elif args.command == "approve":
            articles = approve(args.run, args.selection)
            print(f"Approved {len(articles)} article(s):")
            for a in articles:
                print(f"  {a['n']}. {a['title']}  ({a.get('workspace')})")
        else:
            show(args.run)
    except StepRefused as exc:
        raise SystemExit(f"Refused: {exc}")


if __name__ == "__main__":
    main()

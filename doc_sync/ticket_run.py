"""Phase 1 of a ticket run, the plan and its approval: the I2P agent's
"IA Plan -> Peer review -> approval" loop, for doc-sync's job of finding
the existing articles a change has made wrong.

    python3 doc_sync/ticket_run.py intake  <run> [--provider gemini]        # To Do -> In Draft
    python3 doc_sync/ticket_run.py phase1  <run> [--discovery both]         # In Draft -> Peer review + plan
    python3 doc_sync/ticket_run.py replan  <run> "<feedback>" [--product-lines ...] [--old-terms "..."]
    python3 doc_sync/ticket_run.py approve <run> "1, 3, 5-7" | all          # Peer review -> For review
    python3 doc_sync/ticket_run.py phase2  <run> [--archived-targets "<link>, ..." --confirm-overwrite]
    python3 doc_sync/ticket_run.py show    <run>

- PHASE 2 (For review) assesses each approved article against the change
  and, for one that needs an edit, saves its before/after HTML in
  out/articles/ and either keeps it there or writes it into one of the
  writer's Archived scratch articles (archived_writer.py; never a live
  article). The live article's own draft check runs first: an article with
  an unpublished draft is a manual merge, never written over. Results are
  saved after every article (results.json), so re-running phase 2 retries
  only what failed. The final comment lists every article's outcome; the
  ticket stays in For review, as on the I2P board.

- PHASE 1 runs discovery (kb_search.py) on the change note intake saved,
  within the ticket's product lines, and records the result as a numbered
  "candidate plan" comment, moving the ticket In Draft -> Peer review. The
  plan itself is saved as plan.json. tag_map.json is NOT used: its ids are
  mock fixtures, never live articles.
- RE-PLAN records the writer's feedback as their comment, re-runs triage
  with that feedback and the numbered plan they saw, and records the
  revised plan. The ticket stays in Peer review. `--product-lines` changes
  the scope for this and later re-plans; `--old-terms` replaces the old
  wording intake stated or suggested, in the saved change note.
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
from change_note import load_change_note, save_change_note


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
    agent = plan["discovery"] == "agent"
    if agent:
        how = f"an agent search that read the articles in {scope}, starting from {plan['scanned']:,} keyword match(es)"
    elif both:
        how = f"a full-text search plus a title check, {plan['scanned']:,} listing(s) in {scope}"
    else:
        how = f"{plan['discovery']} search of {plan['scanned']:,} article(s) in {scope}"
    head = "Here's the revised candidate plan" if revised else "Here's the candidate plan"
    lines = [f"{head} for **{tk['key']}**.", "", f"**Change:** {note.summary}", ""]
    if note.old_terms or note.old_terms_suggested:
        terms = [f"**{t}**" for t in note.old_terms]
        terms += [f"**{t}** (suggested)" for t in note.old_terms_suggested
                  if t.lower() not in [o.lower() for o in note.old_terms]]
        lines += [f"**Old wording searched for:** {', '.join(terms)}", ""]
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
    if agent:
        lines += [
            "**Verdict:** **affected** means the article says something the change makes wrong; "
            "**possibly** means it covers the feature but its text alone doesn't settle it. "
            "**Archive** marks an article whose main subject the change removes: it likely needs "
            "archiving and a redirect, not an edit.",
            "",
            "| # | Article | Workspace | Verdict | Why |",
            "|---|---|---|---|---|",
        ]
        for c in cands:
            verdict = "affected" if c.get("verdict") == "affected" else "possibly"
            if c.get("action") == "archive":
                verdict += ", **archive**"
            lines.append(f"| {c['n']} | {_cell(c['title'])} | {_cell(c.get('workspace'))} | {verdict} | "
                         f"{_cell(c.get('reason'))} |")
    elif both:
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
    if agent and plan.get("agent_fallbacks"):
        where = ", ".join(plan["agent_fallbacks"])
        lines += ["", f"**Note:** the full search didn't finish in **{where}**, so the articles there were "
                      "picked by a quicker keyword search instead and are marked **possibly**. That search "
                      "can miss articles; reply if you expected others."]
    for t in plan.get("swept") or []:
        checked = (f"all **{t['shortlisted']}** articles" if t["shortlisted"] == t.get("total")
                   else f"the **{t['shortlisted']}** closest to the change, of {t.get('total')}")
        lines += ["", f"**{t['type']}:** I checked {checked} about {t['type']}."]
        if t["left_out"]:
            lines.append("Left out as not affected (reply to add any): "
                         + "; ".join(_cell(x) for x in t["left_out"]) + ".")
    lines += [
        "",
        "**Next step:** approve the articles to assess by number, for example `1, 3, 5-7`, or "
        "`all`. That moves the ticket to **For review** and starts the edits. To change the plan "
        "instead, reply with what to change.",
    ]
    return "\n".join(lines)


def _mode(discovery, provider):
    """The discovery mode that will actually run (find_candidates_live's
    own fallbacks): no index -> "titles"; "agent" with a non-Claude
    provider -> "index"."""
    if discovery != "titles" and not kb_search.index_available():
        return "titles"
    if discovery == "agent" and provider != "claude":
        return "index"
    return discovery


def _discover(run, note, discovery, provider, scope_override, revision=None, agent_budget=None):
    """Run discovery and save plan.json. Returns the plan."""
    mode = _mode(discovery, provider)
    scope = kb_search.resolve_scope(note, scope_override, mode)
    _, found, scanned = kb_search.find_candidates_live(
        note, product_lines=scope_override, discovery=discovery, provider=provider, revision=revision,
        agent_budget=agent_budget,
    )
    previous = load_plan(run)
    picked = {c["article_id"] for c in found}
    swept = {}
    for a in scanned:
        if a.get("about"):
            t = swept.setdefault(a["about"], {"type": a["about"], "total": a.get("about_total"),
                                              "shortlisted": 0, "left_out": []})
            t["shortlisted"] += 1
            if a["id"] not in picked:
                t["left_out"].append(a["title"])
    plan = {
        "version": (previous or {}).get("version", 0) + 1,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "discovery": mode,
        "provider": provider,
        "scope": scope,
        "scope_override": scope_override,
        "scanned": len(scanned),
        "swept": list(swept.values()),
        "candidates": [
            {"n": i, "article_id": c["article_id"], "title": c.get("title", ""),
             "workspace": c.get("workspace"), "reason": c.get("reason", ""),
             **({"found_by": c["found_by"]} if c.get("found_by") else {}),
             **{k: c[k] for k in ("verdict", "action", "evidence") if c.get(k)}}
            for i, c in enumerate(found, 1)
        ],
    }
    if mode == "agent":
        import discovery_agent
        report = getattr(discovery_agent.find_candidates_agent, "last_report", None) or {}
        plan["agent_fallbacks"] = [ws for ws, w in (report.get("workspaces") or {}).items() if w.get("fallback")]
        plan["not_affected"] = [{"article_id": a["id"], "title": a["title"], "reason": a.get("verdict_reason")}
                                for a in scanned if a.get("verdict") == "not_affected"]
    _save(run, "plan.json", plan)
    return plan


# --- the steps -----------------------------------------------------------------

# Ticket runs use AGENT discovery by default (2026-11-10): on the two confirmed
# answer keys it found 19 of 20 affected articles against index mode's 17,
# with plans about half the size (eval_recall.py; Launchers + AI Pop-ups).
# It needs the knowledge index and Claude; without either it runs as
# "index" or "titles" (_mode). Before that, "index" was the default (from
# 2026-11-07: on the Display Names ticket it found 12-14 focused candidates
# for ~$0.13 where titles found 101 for ~$0.82).
TICKET_DISCOVERY = "agent"


def run_phase1(run, discovery=TICKET_DISCOVERY, provider=claude_call.DEFAULT_PROVIDER,
               product_lines=None, agent_budget=None):
    """In Draft -> Peer review, with the candidate plan as a comment."""
    rd = ticket.run_dir(run)
    tk = ticket.load_ticket(rd)
    _require_status(tk, ticket.IN_DRAFT, "phase 1")
    if not _path(rd, "change_note.json").exists():
        raise StepRefused(f"{tk['key']} has no change note yet: run intake first.")
    if load_plan(rd):
        raise StepRefused(f"{tk['key']} already has a plan; use replan to change it.")
    note = load_change_note(str(_path(rd, "change_note.json")))

    ticket.record_event(rd, "phase1_start", discovery=discovery, provider=provider,
                        **({"agent_budget_usd": agent_budget} if agent_budget else {}))
    try:
        plan = _discover(rd, note, discovery, provider, product_lines, agent_budget=agent_budget)
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


def set_old_terms(rd, terms):
    """The writer's own old terms replace intake's (stated and suggested
    alike) in the saved change note, so every later search uses them."""
    note = load_change_note(str(_path(rd, "change_note.json")))
    note.old_terms = [t for t in terms if t]
    note.old_terms_suggested = []
    save_change_note(note, str(_path(rd, "change_note.json")))
    ticket.record_event(rd, "old_terms", actor="writer", old_terms=note.old_terms)
    return note


def run_replan(run, feedback, provider=None, product_lines=None, old_terms=None, agent_budget=None):
    """Re-plan from the writer's feedback; the ticket stays in Peer review.
    `old_terms` (a list) replaces the change note's old wording first."""
    rd = ticket.run_dir(run)
    tk = ticket.load_ticket(rd)
    _require_status(tk, ticket.PEER_REVIEW, "a re-plan")
    plan = load_plan(rd)
    if not plan:
        raise StepRefused(f"{tk['key']} has no plan to revise.")
    if old_terms and not (feedback or "").strip():
        feedback = "Search for the old wording: " + ", ".join(old_terms) + "."
    if not (feedback or "").strip():
        raise StepRefused("Say what to change: a re-plan needs feedback.")
    if old_terms:
        set_old_terms(rd, old_terms)
    note = load_change_note(str(_path(rd, "change_note.json")))

    ticket.record_comment(rd, feedback.strip(), label="revision request", actor="writer")
    scope_override = product_lines or plan.get("scope_override")
    revision = {"feedback": feedback, "previous": plan["candidates"]}
    try:
        new_plan = _discover(rd, note, plan["discovery"], provider or plan["provider"], scope_override, revision,
                             agent_budget=agent_budget)
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


# --- phase 2 -------------------------------------------------------------------

# Outcomes that are final: a re-run of phase 2 skips these and retries the rest.
DONE = ("draft_written", "draft_saved", "no_edit", "merge_conflict")

RESULT_LABELS = {
    "draft_written": "Draft written",
    "draft_saved": "Draft saved locally",
    "no_edit": "No edit needed",
    "merge_conflict": "Needs a manual merge",
    "failed": "Failed",
}


def load_results(run):
    p = _path(run, "results.json")
    return json.loads(p.read_text()) if p.exists() else {"articles": {}, "targets_used": []}


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:60] or "article"


class _LocalHTML:
    """A one-article stand-in client, so verify.py can check a draft that
    was only saved locally."""

    def __init__(self, html):
        self.html = html

    def get_article(self, article_id, lang_code="en"):
        return {"data": {"html_content": self.html}}


def _phase2_article(rd, note, a, client, assess, targets, used):
    """Assess one approved article and save or write its draft. Returns its
    result record; never raises for a per-article problem."""
    import draft_writer
    import verify

    base = {"n": a["n"], "article_id": a["article_id"], "title": a["title"], "workspace": a.get("workspace"),
            "at": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        live = client.get_article(a["article_id"])["data"]
        assessment = assess(a["article_id"], note, client=client)
    except Exception as exc:
        return {**base, "outcome": "failed", "error": f"{type(exc).__name__}: {str(exc)[:300]}"}
    base.update(confidence=assessment.confidence, rationale=assessment.rationale)
    if not assessment.needs_edit:
        return {**base, "outcome": "no_edit"}
    if not assessment.updated_html_content:
        return {**base, "outcome": "failed",
                "error": "The model said the article needs an edit but returned no corrected HTML."}

    stem = f"{a['n']:02d}-{_slug(a['title'])}"
    articles_dir = rd / "out" / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)
    (articles_dir / f"{stem}.before.html").write_text(assessment.original_html_content or "")
    (articles_dir / f"{stem}.after.html").write_text(assessment.updated_html_content)
    files = {"before": f"articles/{stem}.before.html", "after": f"articles/{stem}.after.html"}

    # The live article's own draft check, exactly as a live write will
    # need it: in-progress work in Document360 is never overwritten, even
    # though this run only writes to Archived scratch articles.
    if draft_writer.has_pending_draft(live):
        return {**base, **files, "outcome": "merge_conflict",
                "note": "The live article already has an unpublished draft; merge the proposed edit by hand."}

    if targets is None:
        check = verify.verify_article(a["article_id"], note, assessment.original_html_content,
                                      client=_LocalHTML(assessment.updated_html_content))
        return {**base, **files, "outcome": "draft_saved", "warnings": check.warnings}

    free = [t["id"] for t in targets.describe() if t["id"] not in used]
    if not free:
        return {**base, **files, "outcome": "failed", "error": "No Archived target left to write this draft into."}
    try:
        link = targets.write(free[0], live.get("title") or a["title"], assessment.updated_html_content)
        used.append(free[0])
        check = verify.verify_article(free[0], note, assessment.original_html_content, client=targets.client)
    except Exception as exc:
        return {**base, **files, "outcome": "failed", "error": f"{type(exc).__name__}: {str(exc)[:300]}"}
    return {**base, **files, "outcome": "draft_written", "target_id": free[0], "target_link": link,
            "warnings": check.warnings}


def phase2_comment(tk, results, approved):
    """The final comment: what happened to each approved article."""
    rows = [results["articles"][a["article_id"]] for a in approved["articles"]
            if a["article_id"] in results["articles"]]
    counts = {k: sum(1 for r in rows if r["outcome"] == k) for k in RESULT_LABELS}
    summary = ", ".join(f"{counts[k]} {RESULT_LABELS[k].lower()}" for k in RESULT_LABELS if counts[k])
    lines = [
        f"I've worked through the **{len(rows)} approved article(s)** for **{tk['key']}**: {summary}.",
        "",
        "| # | Article | Workspace | Result | Notes |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        result = RESULT_LABELS[r["outcome"]]
        if r["outcome"] == "draft_written":
            result += f": [{r['target_id'][:8]}]({r['target_link']})"
        elif r.get("after"):
            result += f": `{r['after']}`"
        notes = r.get("error") or r.get("note") or r.get("rationale") or ""
        if r.get("warnings"):
            notes += " ⚠ " + "; ".join(r["warnings"])
        conf = f" ({r['confidence']} confidence)" if r.get("confidence") else ""
        lines.append(f"| {r['n']} | {_cell(r['title'])} | {_cell(r.get('workspace'))} | {_cell(result)}{conf} | "
                     f"{_cell(notes)} |")
    lines.append("")
    if counts["draft_written"] or counts["draft_saved"]:
        lines.append("**Next step:** review each draft against its live article before anything is published. "
                     "Nothing was published, and no live article was changed.")
    if counts["merge_conflict"]:
        lines.append("Articles that **need a manual merge** already have an unpublished draft in Document360, "
                     "so I didn't write over it; the proposed edit is saved in the run folder.")
    if counts["failed"]:
        lines.append("Run phase 2 again to retry the **failed** article(s); the others are not redone.")
    return "\n".join(lines)


def run_phase2(run, provider=claude_call.DEFAULT_PROVIDER, archived_links=None, confirm_overwrite=False,
               client=None, assess=None):
    """For review: assess each approved article, save or write its draft,
    record the final comment. The ticket stays in For review.

    `archived_links`: the writer's Archived scratch articles to write the
    drafts into (archived_writer.py). Without them, drafts are saved only
    in the run folder. With them, nothing is written unless
    `confirm_overwrite` is True: without it, every target is read, checked
    and NAMED, and the run stops, so the writer can confirm what will be
    overwritten. `client` and `assess` are for tests."""
    rd = ticket.run_dir(run)
    tk = ticket.load_ticket(rd)
    _require_status(tk, ticket.FOR_REVIEW, "phase 2")
    approved = load_approved(rd)
    if not approved:
        raise StepRefused(f"{tk['key']} has no approved articles.")
    results = load_results(rd)
    todo = [a for a in approved["articles"]
            if results["articles"].get(a["article_id"], {}).get("outcome") not in DONE]
    if not todo:
        raise StepRefused(f"Phase 2 is already complete for {tk['key']}; see its final comment.")
    note = load_change_note(str(_path(rd, "change_note.json")))

    if assess is None:
        if provider == "gemini":
            from assess_gemini import assess_article as assess
        else:
            from assess import assess_article as assess
    if client is None:
        from d360_client import Document360Client
        client = Document360Client()

    targets = None
    if archived_links:
        from archived_writer import ArchivedTargets, ArchivedWriteRefused
        targets = ArchivedTargets(archived_links, client=client)
        try:
            described = targets.describe()
        except ArchivedWriteRefused as exc:
            raise StepRefused(str(exc))
        free = [t for t in described if t["id"] not in results["targets_used"]]
        if len(free) < len(todo):
            raise StepRefused(f"{len(todo)} article(s) still to do but only {len(free)} unused Archived target(s) "
                              "listed. Add more links (one per approved article) before running phase 2.")
        if not confirm_overwrite:
            names = "\n".join(f"  - {t['title']!r}  ({t['link']})" for t in free)
            raise StepRefused("These Archived articles would be OVERWRITTEN, content and title, with no undo:\n"
                              f"{names}\nRun again with --confirm-overwrite once the writer has agreed.")

    ticket.record_event(rd, "phase2_start", provider=provider, articles=[a["n"] for a in todo],
                        archived=bool(targets))
    used = results["targets_used"]
    for a in todo:
        print(f"\n  [{a['n']}] {a['title']} ({a.get('workspace')})", flush=True)
        r = _phase2_article(rd, note, a, client, assess, targets, used)
        print(f"      -> {RESULT_LABELS[r['outcome']]}" + (f": {r['error']}" if r.get("error") else ""), flush=True)
        results["articles"][a["article_id"]] = r
        results["targets_used"] = used
        _save(rd, "results.json", results)  # after EVERY article, so a crash loses nothing done
    ticket.record_comment(rd, phase2_comment(tk, results, approved), label="drafts ready")
    ticket.record_event(rd, "phase2_done", outcomes={a["n"]: results["articles"][a["article_id"]]["outcome"]
                                                     for a in approved["articles"]
                                                     if a["article_id"] in results["articles"]})
    return results


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
    results = load_results(rd)["articles"]
    if results:
        print("Phase 2:")
        for r in sorted(results.values(), key=lambda r: r["n"]):
            where = r.get("target_link") or r.get("after") or r.get("error") or ""
            print(f"  {r['n']:>3}. {RESULT_LABELS[r['outcome']]:<22} {r['title']}  {where}")


def main():
    parser = argparse.ArgumentParser(description="Phase 1 of a ticket run: plan, revise, approve.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("intake", help="To Do -> In Draft: extract the change note (ticket_intake.py)")
    p.add_argument("run")
    p.add_argument("--provider", choices=claude_call.PROVIDERS, default=claude_call.DEFAULT_PROVIDER)

    p = sub.add_parser("phase1", help="In Draft -> Peer review: find candidates, record the plan")
    p.add_argument("run")
    p.add_argument("--discovery", choices=kb_search.DISCOVERY_MODES, default=TICKET_DISCOVERY,
                   help="'agent' (default): Claude agents search and read a copy of the knowledge base. "
                        "'index': keyword search of article bodies plus triage. 'both': index plus a strict "
                        "title check, merged with a Found by column. 'titles': every title only.")
    p.add_argument("--agent-budget", type=float, default=None,
                   help="Agent discovery budget for the whole ticket, USD (default $DOC_SYNC_AGENT_BUDGET or 5)")
    p.add_argument("--provider", choices=claude_call.PROVIDERS, default=claude_call.DEFAULT_PROVIDER)
    p.add_argument("--product-lines", default=None, help="Override the ticket's product lines (comma-separated)")

    p = sub.add_parser("replan", help="Revise the plan from the writer's feedback")
    p.add_argument("run")
    p.add_argument("feedback", nargs="?", default="",
                   help="The writer's feedback, word for word (optional with --old-terms)")
    p.add_argument("--provider", choices=claude_call.PROVIDERS, default=None)
    p.add_argument("--product-lines", default=None, help="Change the scope (comma-separated)")
    p.add_argument("--old-terms", default=None,
                   help="The writer's old wording (comma-separated), replacing intake's stated and "
                        "suggested old terms")
    p.add_argument("--agent-budget", type=float, default=None,
                   help="Agent discovery budget for this re-plan, USD (default $DOC_SYNC_AGENT_BUDGET or 5)")

    p = sub.add_parser("approve", help="Peer review -> For review: approve plan numbers")
    p.add_argument("run")
    p.add_argument("selection", help='Plan numbers, e.g. "1, 3, 5-7", or "all"')

    p = sub.add_parser("phase2", help="For review: assess approved articles, save or write their drafts")
    p.add_argument("run")
    p.add_argument("--provider", choices=claude_call.PROVIDERS, default=claude_call.DEFAULT_PROVIDER)
    p.add_argument("--archived-targets", default=None,
                   help="Comma-separated Archived portal links to write the drafts into, one per approved "
                        "article. Without it, drafts are saved only in the run folder.")
    p.add_argument("--confirm-overwrite", action="store_true",
                   help="The writer has agreed the listed Archived articles may be overwritten")

    p = sub.add_parser("show", help="Print the ticket's status, plan and approval")
    p.add_argument("run")

    args = parser.parse_args()
    meter = claude_call.CostMeter()
    try:
        with meter:
            _dispatch(args)
    except StepRefused as exc:
        raise SystemExit(f"Refused: {exc}")
    finally:
        _record_cost(args, meter)


def _record_cost(args, meter):
    """What this step spent on model calls, failed ones included: printed
    and logged in out/jira_log.json as a "cost" event. NEVER in a comment,
    the plan or the artifact (writer decision 2026-11-10): those are shared
    with readers who don't need it. build_artifact.py doesn't render "cost"
    events."""
    if not meter.calls:
        return
    try:
        ticket.record_event(ticket.run_dir(args.run), "cost", step=args.command, usd=round(meter.usd, 4),
                            calls=meter.calls)
    except Exception as exc:  # never let bookkeeping hide the step's own outcome
        print(f"    (couldn't log the cost: {exc})")
    print(f"Model cost for {args.command}: ${meter.usd:.2f} over {meter.calls} call(s) "
          "(logged in out/jira_log.json, not shown on the ticket)")


def _dispatch(args):
    """Run one CLI step."""
    if args.command == "intake":
        import ticket_intake
        outcome = ticket_intake.run_intake(args.run, provider=args.provider)
        if outcome["status"] == "bounced":
            raise SystemExit("Bounced to To Do: " + " ".join(outcome["reasons"]))
        print(f"Product lines: {', '.join(outcome['product_lines'])}")
        ticket_intake._print_old_terms(outcome)
    elif args.command == "phase1":
        plan = run_phase1(args.run, args.discovery, args.provider,
                          kb_search.parse_product_lines(args.product_lines), args.agent_budget)
        print(f"Plan v{plan['version']}: {len(plan['candidates'])} candidate(s).")
        show(args.run)
    elif args.command == "replan":
        plan = run_replan(args.run, args.feedback, args.provider,
                          kb_search.parse_product_lines(args.product_lines),
                          kb_search.parse_product_lines(args.old_terms), args.agent_budget)
        print(f"Plan v{plan['version']}: {len(plan['candidates'])} candidate(s).")
        show(args.run)
    elif args.command == "approve":
        articles = approve(args.run, args.selection)
        print(f"Approved {len(articles)} article(s):")
        for a in articles:
            print(f"  {a['n']}. {a['title']}  ({a.get('workspace')})")
    elif args.command == "phase2":
        links = [l.strip() for l in (args.archived_targets or "").split(",") if l.strip()]
        run_phase2(args.run, args.provider, links or None, args.confirm_overwrite)
        show(args.run)
    else:
        show(args.run)


if __name__ == "__main__":
    main()

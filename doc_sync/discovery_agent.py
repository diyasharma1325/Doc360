"""Stage 2 (discovery), "agent" mode: a Claude agent with read-only Grep /
Glob / Read tools searches a plain-text copy of each workspace in scope
(kb_mirror.py), reads the articles it finds in full, and returns a verdict
for each: affected, potentially affected or not affected, with an action
(edit, archive, none) and a quoted line of evidence.

Why it exists: index-mode triage judges each shortlisted article from its
title and a ~30-word excerpt, with no tools. On the Launchers answer key it
was shown all 27 affected articles and left out 6, mostly FAQs and
troubleshooting articles whose excerpt didn't look affected (2026-11-09).
An agent that opens the article doesn't have that blind spot, and can
follow leads (a related setting, another name for the feature) that a
single keyword query never tries.

How a run works:

- One agent per workspace in scope, in parallel, each in its own temporary
  copy of that workspace OUTSIDE the repo (so no CLAUDE.md is loaded, and
  the agent's file tools are confined to that one workspace).
- The index-mode shortlist (kb_search.index_shortlist: content-type sweep
  plus ranked full-text hits) is the agent's MUST-REVIEW list. Every
  article on it must get a verdict. One the agent doesn't return is kept as
  "potentially affected" rather than dropped, so nothing the index found
  can disappear silently.
- AGENT_RUNS independent runs per workspace, merged by _merge(): the most
  cautious verdict wins, because one run varies and a miss costs more than
  an extra article to review.
- A PER-TICKET BUDGET (TICKET_BUDGET_USD, or $DOC_SYNC_AGENT_BUDGET) decides
  how many runs happen (plan_runs below). When it covers two full runs in
  every workspace, they all run at once. Otherwise run 1 goes out everywhere
  first, and what's left decides, per workspace, between a full second run,
  a cheaper RECHECK (re-judge only the must-review articles run 1 cleared,
  no new searching) and nothing.
- FILL: a run that leaves must-review articles unjudged gets one short
  follow-up for just those (FILL_CAP_USD), while the ticket budget has
  room; only what's still unjudged after that is kept as "possibly".
- FALLBACK: a workspace where no run succeeded (an error, or a run that hit
  its cap) is triaged the index-mode way over its must-review list instead
  (kb_search.triage_shortlist), and the plan says so. A failed second run
  just leaves run 1's verdicts.
- Affected and potentially affected articles are the candidates. The
  not-affected verdicts are returned too, with their reasons, so the plan
  can show what was checked and ruled out.

Read-only end to end: the local index and the copy are only read. Costs
model calls (claude -p on the writer's login), capped per run by the CLI's
--max-budget-usd (RUN_CAP_USD / RECHECK_CAP_USD) and per ticket as above.
Costs go to the call log and the caller's cost meter, never the plan.

    python3 doc_sync/discovery_agent.py <change_note.json> [--product-lines "DAP for Web"]
"""
import argparse
import json
import os
import re
import shutil
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import claude_call
import kb_index
import kb_mirror
import kb_search
import product_context
from change_note import load_change_note

THIS_DIR = Path(__file__).resolve().parent
PROMPT_PATH = THIS_DIR / "prompts" / "discovery_agent.md"

AGENT_MODEL = claude_call.DEFAULT_MODEL
AGENT_MAX_OUTPUT_TOKENS = 32000

# Budget. Measured full runs cost $0.19-0.35 (DAP for Web, 48-85 must-review
# articles, 2026-11-10), so RUN_CAP_USD leaves ~3x headroom. The CLI checks a
# cap only between turns, so a run can end up to CAP_OVERSHOOT_USD over it.
TICKET_BUDGET_USD = float(os.environ.get("DOC_SYNC_AGENT_BUDGET") or 5.0)
RUN_CAP_USD = 1.00
RECHECK_CAP_USD = 0.50
CAP_OVERSHOOT_USD = 0.25
MIN_RUN_CAP_USD = 0.25
MIN_RECHECK_USD = 0.15
SECOND_RUN_MARGIN = 1.3  # a full second run needs ~1.3x what run 1 cost there
# A run can return without judging every must-review article: on the AI
# Pop-ups ticket both runs once skipped 62 of 85 (2026-11-10), which the
# safety net turned into 62 "possibly affected" rows. So a FILL pass asks
# for just the missing ones, if the ticket budget still has room.
FILL_CAP_USD = 0.40
MAX_PARALLEL = 4
# Independent runs per workspace, merged. One run varies: on the Launchers key
# the first run found 2 affected articles the second didn't (2026-11-10).
AGENT_RUNS = 2

VERDICTS = ("affected", "potentially_affected", "not_affected")
ACTIONS = ("edit", "archive", "none")
CANDIDATE_VERDICTS = ("affected", "potentially_affected")

SCHEMA = {
    "type": "object",
    "properties": {
        "searches": {"type": "array", "items": {"type": "string"}},
        "articles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "verdict": {"type": "string", "enum": list(VERDICTS)},
                    "action": {"type": "string", "enum": list(ACTIONS)},
                    "evidence": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["path", "verdict", "action", "reason"],
            },
        },
    },
    "required": ["searches", "articles"],
}


def _system_prompt(workspace):
    parts = [PROMPT_PATH.read_text()]
    parts.extend(product_context.prompt_parts_for_lines([workspace]))
    return "\n".join(parts)


_FILL_NOTE = (
    "FILL PASS. An earlier pass didn't give a verdict on the articles below. Open each one, grep it "
    "for the feature's names and the old wording, and give every one of them a verdict. Search only "
    "within these articles; don't look for new ones."
)

_RECHECK_NOTE = (
    "RECHECK PASS. An earlier pass judged every article below NOT affected. Second opinions catch "
    "what one pass misses, so open each one in full, grep it for the feature's names and the old "
    "wording, and give it a fresh verdict. Search only within these articles; don't look for new ones."
)


def _request(change_note, workspace, seeds, paths, revision, recheck=False):
    """`recheck` is False (a full run), True (recheck pass) or "fill"."""
    lines = kb_search.note_block(change_note)
    if revision:
        lines.append(kb_search._revision_block(revision).strip())
    if recheck:
        lines += ["", _FILL_NOTE if recheck == "fill" else _RECHECK_NOTE]
    lines += ["", f"Workspace: {workspace}", "",
              f"Must review ({len(seeds)} article(s){'' if recheck else ' a keyword index found'}). "
              f"Your `articles` list must have an entry for EACH of these {len(seeds)} paths, with a "
              "verdict, as well as anything else you find:"]
    for a in seeds:
        about = f"  [about: {a['about']}]" if a.get("about") else ""
        lines.append(f"- {paths[a['id']]}  ({a['title']}){about}")
    if not seeds:
        lines.append("- (none: the keyword index matched nothing here; search for yourself)")
    return "\n".join(lines)


def _norm(path, root):
    """The agent's path, relative to its working directory."""
    p = (path or "").strip().strip("`")
    if p.startswith(str(root)):
        p = p[len(str(root)):]
    elif "/" + root.name + "/" in p:  # absolute path through a resolved temp dir (/private/var/...)
        p = p.split("/" + root.name + "/", 1)[1]
    return re.sub(r"^(\./|/)+", "", p)


def _run_workspace(change_note, workspace, seeds, revision, model, run=1, cap=RUN_CAP_USD, recheck=False):
    """One agent run over one workspace -> (records, searches). Must-review
    articles it gave no verdict on are handled by _merge(). `recheck` makes
    it a recheck pass over `seeds` only. Raises ClaudeCallError."""
    manifest = kb_mirror.manifest()
    prefix = workspace + "/"
    by_path = {rel[len(prefix):]: aid for aid, rel in manifest.items() if rel.startswith(prefix)}
    path_of = {aid: p for p, aid in by_path.items()}
    seeds = [a for a in seeds if a["id"] in path_of]

    tmp = Path(tempfile.mkdtemp(prefix="doc_sync_agent_"))
    root = tmp / "kb"
    try:
        shutil.copytree(kb_mirror.DEFAULT_MIRROR_PATH / workspace, root)
        result = claude_call.generate(
            system=_system_prompt(workspace),
            user=_request(change_note, workspace, seeds, path_of, revision, recheck=recheck),
            schema=SCHEMA, label=f"agent discovery: {workspace} #{run}"
                                f"{(' (' + ('fill' if recheck == 'fill' else 'recheck') + ')') if recheck else ''}",
            model=model, max_tokens=AGENT_MAX_OUTPUT_TOKENS, tools=claude_call.READ_ONLY_TOOLS, cwd=str(root),
            budget_usd=round(cap, 2),
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    titles = {a["id"]: a["title"] for a in seeds}
    records, seen, unknown = [], set(), []
    for a in result.get("articles") or []:
        aid = by_path.get(_norm(a.get("path"), root))
        if not aid:
            unknown.append(a.get("path"))
            continue
        if aid in seen:
            continue
        seen.add(aid)
        records.append({
            "article_id": aid, "title": titles.get(aid) or _title_of(manifest[aid]), "workspace": workspace,
            "verdict": a["verdict"], "action": a["action"] if a["verdict"] != "not_affected" else "none",
            "evidence": a.get("evidence", ""), "reason": a.get("reason", ""),
            "found_by": "index+agent" if aid in titles else "agent",
        })
    if unknown:
        print(f"    ({workspace}: ignored {len(unknown)} path(s) not in the copy: {unknown[:5]})")
    return records, result.get("searches") or []


def _title_of(rel):
    try:
        first = (kb_mirror.DEFAULT_MIRROR_PATH / rel).read_text(encoding="utf-8").split("\n", 1)[0]
        return first.lstrip("# ").strip()
    except OSError:
        return rel.rsplit("/", 1)[-1]


RANK = {"affected": 0, "potentially_affected": 1, "not_affected": 2}


def _merge(runs, seeds, workspace):
    """One record per article from several runs: the most cautious verdict
    wins (affected > potentially affected > not affected), with that run's
    reason, evidence and action; `runs_flagged` counts the runs that put it
    in the plan. A must-review article NO run judged is kept as potentially
    affected, so nothing the index found can disappear silently."""
    best, flagged = {}, {}
    for records in runs:
        for r in records:
            aid = r["article_id"]
            if r["verdict"] in CANDIDATE_VERDICTS:
                flagged[aid] = flagged.get(aid, 0) + 1
            if aid not in best or RANK[r["verdict"]] < RANK[best[aid]["verdict"]]:
                best[aid] = r
    merged = [{**r, "runs_flagged": flagged.get(r["article_id"], 0), "runs": len(runs)} for r in best.values()]
    missing = [a for a in seeds if a["id"] not in best]
    if missing:
        print(f"    ({workspace}: no run gave a verdict on {len(missing)} must-review article(s); "
              "kept as potentially affected)")
    for a in missing:
        merged.append({
            "article_id": a["id"], "title": a["title"], "workspace": workspace, "verdict": "potentially_affected",
            "action": "edit", "evidence": "", "reason": "On the keyword shortlist, but the agent returned no "
            "verdict for it; kept so it can't be dropped silently.", "found_by": "index",
            "runs_flagged": 0, "runs": len(runs),
        })
    return merged


ORDER = {("affected", "archive"): 0, ("affected", "edit"): 1, ("potentially_affected", "archive"): 2,
         ("potentially_affected", "edit"): 3}


class _Spend:
    """What the ticket's agent runs have spent so far, shared by the pool's
    threads, so a fill pass only starts if the budget still has room."""

    def __init__(self, budget):
        self.budget, self.usd = budget, 0.0
        self._lock = threading.Lock()

    def add(self, usd):
        with self._lock:
            self.usd += usd or 0.0

    def reserve(self, cap):
        """True (and counts `cap` as spent until settle()) if it fits."""
        with self._lock:
            if self.usd + cap + CAP_OVERSHOOT_USD > self.budget:
                return False
            self.usd += cap
            return True

    def settle(self, reserved, actual):
        with self._lock:
            self.usd += (actual or 0.0) - reserved


def _job(change_note, ws, seeds, revision, model, run, cap, recheck=False, spend=None):
    """One run, never raising: {ok, kind, records, searches, cost, error}.
    A run that leaves must-review articles unjudged gets one fill pass for
    them, if `spend` says the ticket budget has room for FILL_CAP_USD."""
    claude_call.take_last_cost()  # this pool thread may have run another job before
    kind = "recheck" if recheck else "full"
    try:
        records, searches = _run_workspace(change_note, ws, seeds, revision, model, run, cap, recheck)
        cost = claude_call.take_last_cost()
        if spend:
            spend.add(cost)
        judged = {r["article_id"] for r in records}
        missing = [a for a in seeds if a["id"] not in judged]
        if missing and spend and spend.reserve(FILL_CAP_USD):
            print(f"    ({ws}: run #{run} left {len(missing)} must-review article(s) unjudged — "
                  "asking for just those)")
            fill_cost = 0.0
            try:
                more, _ = _run_workspace(change_note, ws, missing, revision, model, run, FILL_CAP_USD, "fill")
                records = records + [r for r in more if r["article_id"] not in judged]
            except claude_call.ClaudeCallError as exc:
                print(f"    ({ws}: fill pass for run #{run} failed: {exc})")
            finally:
                fill_cost = claude_call.take_last_cost()
                spend.settle(FILL_CAP_USD, fill_cost)
            cost += fill_cost
        return {"ok": True, "kind": kind, "records": records, "searches": searches, "cost": cost}
    except claude_call.ClaudeCallError as exc:
        print(f"    ({ws}: agent run #{run} failed: {exc})")
        cost = claude_call.take_last_cost()
        if spend:
            spend.add(cost)
        return {"ok": False, "kind": kind, "records": [], "searches": [], "cost": cost,
                "error": str(exc)[:300], "budget": isinstance(exc, claude_call.BudgetExceeded)}


def plan_runs(n_workspaces, budget, runs=AGENT_RUNS):
    """How the first round goes: (all_at_once, run1_cap). All at once means
    `runs` full runs per workspace in parallel, each capped at RUN_CAP_USD;
    otherwise one run per workspace first, at run1_cap each, and round two
    is decided from what's left (_second_round)."""
    per_ws = budget / max(n_workspaces, 1)
    if runs >= 2 and per_ws >= runs * (RUN_CAP_USD + CAP_OVERSHOOT_USD):
        return True, RUN_CAP_USD
    return False, max(MIN_RUN_CAP_USD, min(RUN_CAP_USD, per_ws - CAP_OVERSHOOT_USD))


def _second_round(scope, first, by_ws, remaining):
    """Per workspace, what round two can afford out of `remaining`, shared
    equally: {ws: ("full" | "recheck", cap, seeds)}; a workspace left out
    gets nothing more. Only a workspace whose run 1 succeeded gets one, so
    the budget is shared among those."""
    eligible = [ws for ws in scope if first[ws]["ok"]]
    share = remaining / max(len(eligible), 1) - CAP_OVERSHOOT_USD
    out = {}
    for ws in scope:
        r1 = first[ws]
        if not r1["ok"]:
            continue
        if share >= max(MIN_RUN_CAP_USD, r1["cost"] * SECOND_RUN_MARGIN):
            out[ws] = ("full", min(RUN_CAP_USD, share), by_ws[ws])
            continue
        verdicts = {r["article_id"]: r["verdict"] for r in r1["records"]}
        cleared = [a for a in by_ws[ws] if verdicts.get(a["id"]) == "not_affected"]
        if cleared and share >= MIN_RECHECK_USD:
            out[ws] = ("recheck", min(RECHECK_CAP_USD, share), cleared)
    return out


def _fallback(change_note, ws, seeds, revision):
    """Index-mode triage over a workspace's must-review list, for when no
    agent run there succeeded. Raises if this fails too."""
    picked = kb_search.triage_shortlist(change_note, seeds, [ws], revision=revision,
                                        label=f"fallback triage: {ws}") if seeds else []
    return [{**c, "workspace": ws, "verdict": "potentially_affected", "action": "edit", "evidence": "",
             "found_by": "index (agent fallback)", "runs_flagged": 0, "runs": 0} for c in picked]


def find_candidates_agent(change_note, scope, revision=None, model=AGENT_MODEL, db_path=kb_index.DEFAULT_DB_PATH,
                          runs=AGENT_RUNS, budget_usd=None):
    """Agent discovery over the workspaces in `scope` (live workspace names),
    within `budget_usd` for the whole ticket (default TICKET_BUDGET_USD).
    Same return shape as kb_search.find_candidates_live(): (article_ids,
    candidate_records, scanned). Candidates are the affected and
    potentially affected articles, each with verdict, action, evidence,
    reason and found_by; `scanned` is the must-review shortlist, each entry
    also carrying the agent's verdict, so not-affected ones show with their
    reasons. find_candidates_agent.last_report says how each workspace was
    searched, including any fallback."""
    budget = TICKET_BUDGET_USD if budget_usd is None else float(budget_usd)
    kb_mirror.ensure_fresh(db_path=db_path)
    shortlist = kb_search.index_shortlist(change_note, scope, db_path=db_path, revision=revision)
    by_ws = {ws: [a for a in shortlist if a.get("workspace") == ws] for ws in scope}

    all_at_once, cap1 = plan_runs(len(scope), budget, runs)
    spend = _Spend(budget)
    jobs = {ws: [] for ws in scope}
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        if all_at_once:
            futs = {(ws, i): pool.submit(_job, change_note, ws, by_ws[ws], revision, model, i, cap1, False, spend)
                    for ws in scope for i in range(1, runs + 1)}
            for (ws, _), f in futs.items():
                jobs[ws].append(f.result())
        else:
            print(f"    (agent budget ${budget:.2f} for {len(scope)} workspace(s): run 1 everywhere first, "
                  "then a second run or a recheck where the budget allows)")
            futs = {ws: pool.submit(_job, change_note, ws, by_ws[ws], revision, model, 1, cap1, False, spend)
                    for ws in scope}
            first = {ws: f.result() for ws, f in futs.items()}
            for ws in scope:
                jobs[ws].append(first[ws])
            if runs >= 2:
                spent = sum(j["cost"] for j in first.values())
                second = _second_round(scope, first, by_ws, budget - spent)
                futs = {ws: pool.submit(_job, change_note, ws, seeds, revision, model, 2, cap, kind == "recheck", spend)
                        for ws, (kind, cap, seeds) in second.items()}
                for ws, f in futs.items():
                    jobs[ws].append(f.result())
                skipped = [ws for ws in scope if ws not in second and first[ws]["ok"]]
                if skipped:
                    print(f"    (no budget left for a second pass in: {', '.join(skipped)})")

    records, searches, report = [], {}, {"budget_usd": budget, "all_at_once": all_at_once, "workspaces": {}}
    for ws in scope:
        ok = [j for j in jobs[ws] if j["ok"]]
        searches[ws] = [j["searches"] for j in ok]
        info = {"runs": [{k: j.get(k) for k in ("kind", "ok", "error", "budget")} for j in jobs[ws]],
                "fallback": not ok}
        if ok:
            records.extend(_merge([j["records"] for j in ok], by_ws[ws], ws))
        else:
            print(f"    ({ws}: no agent run succeeded — falling back to keyword-search triage there)")
            records.extend(_fallback(change_note, ws, by_ws[ws], revision))
        report["workspaces"][ws] = info
    report["spent_usd"] = round(sum(j["cost"] for js in jobs.values() for j in js), 4)

    verdict_of = {r["article_id"]: r for r in records}
    scanned = [{**a, "verdict": verdict_of.get(a["id"], {}).get("verdict"),
                "verdict_reason": verdict_of.get(a["id"], {}).get("reason")} for a in shortlist]
    found = [r for r in records if r["verdict"] in CANDIDATE_VERDICTS]
    found.sort(key=lambda r: ORDER.get((r["verdict"], r["action"]), 9))
    counts = {v: sum(1 for r in records if r["verdict"] == v) for v in VERDICTS}
    archive = sum(1 for r in found if r["action"] == "archive")
    split = sum(1 for r in found if r["runs"] and r["runs_flagged"] < r["runs"])
    print(f"    (agent: {counts['affected']} affected, {counts['potentially_affected']} potentially affected "
          f"({archive} to archive), {counts['not_affected']} checked and not affected; "
          f"{split} flagged by only some runs; agent spend ${report['spent_usd']:.2f} of ${budget:.2f})")
    find_candidates_agent.last_searches = searches
    find_candidates_agent.last_not_affected = [r for r in records if r["verdict"] == "not_affected"]
    find_candidates_agent.last_report = report
    return [r["article_id"] for r in found], found, scanned


def main():
    p = argparse.ArgumentParser(description="Run agent discovery on a change note (read-only, model calls).")
    p.add_argument("change_note")
    p.add_argument("--product-lines", help='e.g. "DAP for Web, DAP for Desktop" (default: the note\'s own)')
    p.add_argument("--model", default=AGENT_MODEL)
    p.add_argument("--runs", type=int, default=AGENT_RUNS)
    p.add_argument("--budget", type=float, default=TICKET_BUDGET_USD, help="Agent budget for the whole ticket, USD")
    args = p.parse_args()
    note = load_change_note(args.change_note)
    scope = kb_search.resolve_scope(note, kb_search.parse_product_lines(args.product_lines), "index")
    _, found, _ = find_candidates_agent(note, scope, model=args.model, runs=args.runs, budget_usd=args.budget)
    for i, c in enumerate(found, 1):
        print(f"{i:>3}. [{c['verdict']}/{c['action']}] {c['title']}  ({c['workspace']}, {c['found_by']})")
        print(f"       {c['reason']}")
    print(json.dumps(find_candidates_agent.last_searches, indent=1))


if __name__ == "__main__":
    main()

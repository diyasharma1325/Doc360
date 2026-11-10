"""Discovery recall benchmark: how many of the articles a change really
affects does discovery find? Scored against answer keys a writer
confirmed, so a change to search is measured, not judged by feel.

    python3 doc_sync/eval_recall.py                      # every key, shortlist stage only (free)
    python3 doc_sync/eval_recall.py --triage             # also the plan (model calls, ~$0.10-0.50 per key)
    python3 doc_sync/eval_recall.py launchers-content-tab --triage
    python3 doc_sync/eval_recall.py launchers-content-tab --triage --discovery agent   # agent mode's plan

Two stages are scored, because they fail differently:

- SHORTLIST recall: the expected articles that reach the shortlist the
  model is shown (local search only, no model call, no cost). An article
  missing here can never be found, however good the model is.
- PLAN recall (--triage): the expected articles in the candidate plan,
  after the model's triage. The gap between the two is the model leaving
  out what it was shown.

Plan size is reported beside recall; articles in the plan but not in the
key are listed as "extra", not scored as wrong: a key lists what must be
found, and a reviewer may decide an extra belongs in it.

ANSWER KEYS are doc_sync/eval/keys/<name>.json:

    {"name": "...", "status": "draft" | "confirmed", "reviewed_by": "...",
     "notes": "...", "ticket": {"summary": ..., "description": ...},
     "change_note": {... as intake saved it ...},
     "expected": [{"article_id": ..., "title": ..., "category_path": ...}, ...],
     "not_affected": [... same shape: reviewed and ruled out; optional ...],
     "ignore": [... same shape: left out of scoring entirely; optional ...]}

An `expected` entry may carry "action": "archive" (the article should be
archived, not edited); agent mode's archive flags are scored against it.

A plan's articles outside `expected` are split into "wrong" (on the key's
`not_affected` list) and "extra" (nobody has reviewed them yet).

A key's `status` is printed with its score: a draft key's recall is only
as good as the draft. Results are saved to doc_sync/eval/results/
(git-ignored) so runs can be compared.

Read-only: the local index, plus model calls with --triage.
"""
import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
KEYS_DIR = THIS_DIR / "eval" / "keys"
RESULTS_DIR = THIS_DIR / "eval" / "results"

import discovery_agent
import kb_index
import kb_search
from change_note import load_change_note


def load_key(path):
    key = json.loads(Path(path).read_text())
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(key["change_note"], f)
    key["_note"] = load_change_note(f.name)
    Path(f.name).unlink()
    return key


def shortlist_of(note, scope):
    """The shortlist index-mode triage (and agent mode's must-review list)
    starts from: local search only, no model call."""
    return kb_search.index_shortlist(note, scope)


def score(key, triage=False, provider="claude", discovery="index"):
    note = key["_note"]
    scope = kb_search.resolve_scope(note, None, "index")
    expected = {e["article_id"]: e["title"] for e in key["expected"]}
    out = {"name": key["name"], "status": key.get("status", "draft"), "expected": len(expected),
           "scope": scope}

    shortlist = shortlist_of(note, scope)
    shown = {a["id"] for a in shortlist}
    out["shortlist_size"] = len(shortlist)
    out["shortlist_found"] = sorted(t for i, t in expected.items() if i in shown)
    out["shortlist_missed"] = sorted(t for i, t in expected.items() if i not in shown)

    if triage:
        t0 = time.time()
        out["discovery"] = discovery
        if discovery == "agent":
            _, found, _ = discovery_agent.find_candidates_agent(note, scope)
            out["verdicts"] = {i: {"title": t, **next(({"verdict": c["verdict"], "action": c["action"],
                                                          "reason": c["reason"]} for c in found
                                                         if c["article_id"] == i), {"verdict": None})}
                               for i, t in expected.items()}
            out["not_affected"] = [{"title": r["title"], "reason": r["reason"]}
                                   for r in discovery_agent.find_candidates_agent.last_not_affected]
            out["searches"] = discovery_agent.find_candidates_agent.last_searches
        else:
            _, found, _ = kb_search.find_candidates_indexed(note, scope=scope, provider=provider)
        ignored = {e["article_id"] for e in key.get("ignore") or []}
        picked = {c["article_id"]: c["title"] for c in found if c["article_id"] not in ignored}
        # Archive check (agent mode carries an action): expected archive
        # articles flagged as archive, and anything else flagged as archive.
        if any("action" in c for c in found):
            to_archive = {e["article_id"]: e["title"] for e in key["expected"] if e.get("action") == "archive"}
            flagged = {c["article_id"]: c["title"] for c in found if c.get("action") == "archive"}
            out["archive_found"] = sorted(t for i, t in to_archive.items() if i in flagged)
            out["archive_missed"] = sorted(t for i, t in to_archive.items() if i not in flagged)
            out["archive_wrong"] = sorted(t for i, t in flagged.items() if i not in to_archive and i not in ignored)
        out["plan_size"] = len(picked)
        out["plan_found"] = sorted(t for i, t in expected.items() if i in picked)
        out["plan_missed"] = sorted(t for i, t in expected.items() if i not in picked)
        ruled_out = {e["article_id"] for e in key.get("not_affected") or []}
        out["plan_extra"] = sorted(t for i, t in picked.items() if i not in expected and i not in ruled_out)
        out["plan_wrong"] = sorted(t for i, t in picked.items() if i in ruled_out)
        out["plan_seconds"] = round(time.time() - t0, 1)
    return out


def _pct(n, d):
    return f"{n}/{d} ({100 * n / d:.0f}%)" if d else "-"


def report(r):
    print(f"\n== {r['name']}  [{r['status']} key, {r['expected']} expected, scope: {', '.join(r['scope'])}]")
    print(f"   shortlist recall: {_pct(len(r['shortlist_found']), r['expected'])}"
          f"   (shortlist of {r['shortlist_size']})")
    for t in r["shortlist_missed"]:
        print(f"      never shown: {t}")
    if "plan_size" in r:
        print(f"   plan recall:      {_pct(len(r['plan_found']), r['expected'])}"
              f"   (plan of {r['plan_size']}, {r['discovery']} mode, {r['plan_seconds']}s)")
        for t in r["plan_missed"]:
            if t not in r["shortlist_missed"]:
                print(f"      shown, left out: {t}")
            elif r["discovery"] == "agent":
                print(f"      never found: {t}")
        if "archive_found" in r:
            n = len(r["archive_found"]) + len(r["archive_missed"])
            print(f"   archive flags:    {_pct(len(r['archive_found']), n)}"
                  + (f", {len(r['archive_wrong'])} wrongly flagged" if r["archive_wrong"] else ""))
            for t in r["archive_missed"]:
                print(f"      not flagged for archive: {t}")
            for t in r["archive_wrong"]:
                print(f"      flagged for archive, shouldn't be: {t}")
        if r.get("plan_wrong"):
            print(f"   wrong (in plan, reviewed as not affected): {len(r['plan_wrong'])}")
            for t in r["plan_wrong"]:
                print(f"      x {t}")
        if r["plan_extra"]:
            print(f"   extra (in plan, not reviewed yet): {len(r['plan_extra'])}")
            for t in r["plan_extra"]:
                print(f"      + {t}")


def main():
    parser = argparse.ArgumentParser(description="Score discovery recall against answer keys.")
    parser.add_argument("keys", nargs="*", help="Key names (default: every key in doc_sync/eval/keys/)")
    parser.add_argument("--triage", action="store_true", help="Also run triage and score the plan (model calls)")
    parser.add_argument("--provider", default="claude", choices=("claude", "gemini"))
    parser.add_argument("--discovery", default="index", choices=("index", "agent"),
                        help="Which mode's plan --triage scores (agent: Claude agents over kb_mirror)")
    args = parser.parse_args()

    st = kb_index.status()
    if not st.get("exists"):
        raise SystemExit("No knowledge index; build one first: python3 doc_sync/kb_index.py build")
    print(f"Index: built {st['built_at']} ({st['age_hours']}h ago), {st['articles']} articles, "
          f"body = {st.get('body_includes', 'text')}")

    paths = [KEYS_DIR / f"{k}.json" for k in args.keys] or sorted(KEYS_DIR.glob("*.json"))
    if not paths:
        raise SystemExit(f"No answer keys in {KEYS_DIR}")
    results = []
    for path in paths:
        r = score(load_key(path), triage=args.triage, provider=args.provider, discovery=args.discovery)
        report(r)
        results.append(r)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps({"index": st, "triage": args.triage, "results": results}, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()

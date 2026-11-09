"""Discovery recall benchmark: how many of the articles a change really
affects does discovery find? Scored against answer keys a writer
confirmed, so a change to search is measured, not judged by feel.

    python3 doc_sync/eval_recall.py                      # every key, shortlist stage only (free)
    python3 doc_sync/eval_recall.py --triage             # also the plan (model calls, ~$0.10-0.50 per key)
    python3 doc_sync/eval_recall.py launchers-content-tab --triage

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
     "expected": [{"article_id": ..., "title": ..., "category_path": ...}, ...]}

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
from unittest import mock

THIS_DIR = Path(__file__).resolve().parent
KEYS_DIR = THIS_DIR / "eval" / "keys"
RESULTS_DIR = THIS_DIR / "eval" / "results"

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
    """The shortlist find_candidates_indexed() would hand triage, with
    triage stubbed out: no model call."""
    with mock.patch.object(kb_search, "triage", return_value=[]):
        _, _, shortlist = kb_search.find_candidates_indexed(note, scope=scope)
    return shortlist


def score(key, triage=False, provider="claude"):
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
        _, found, _ = kb_search.find_candidates_indexed(note, scope=scope, provider=provider)
        picked = {c["article_id"]: c["title"] for c in found}
        out["plan_size"] = len(picked)
        out["plan_found"] = sorted(t for i, t in expected.items() if i in picked)
        out["plan_missed"] = sorted(t for i, t in expected.items() if i not in picked)
        out["plan_extra"] = sorted(t for i, t in picked.items() if i not in expected)
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
              f"   (plan of {r['plan_size']}, {r['plan_seconds']}s)")
        for t in r["plan_missed"]:
            if t not in r["shortlist_missed"]:
                print(f"      shown, left out: {t}")
        if r["plan_extra"]:
            print(f"   extra (in plan, not in key): {len(r['plan_extra'])}")
            for t in r["plan_extra"]:
                print(f"      + {t}")


def main():
    parser = argparse.ArgumentParser(description="Score discovery recall against answer keys.")
    parser.add_argument("keys", nargs="*", help="Key names (default: every key in doc_sync/eval/keys/)")
    parser.add_argument("--triage", action="store_true", help="Also run triage and score the plan (model calls)")
    parser.add_argument("--provider", default="claude", choices=("claude", "gemini"))
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
        r = score(load_key(path), triage=args.triage, provider=args.provider)
        report(r)
        results.append(r)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps({"index": st, "triage": args.triage, "results": results}, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()

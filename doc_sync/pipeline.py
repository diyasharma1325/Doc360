"""MVP orchestrator: run a change note through candidate lookup,
assessment, and draft generation (stages 1-4 wired end to end), then work
the review queue (stage 5) from the same CLI.

Current defaults, as of this standing decision — not a fallback, the
actual setup until told otherwise:
  - Gemini is the PRIMARY provider (assess_gemini.py), not a substitute.
    Pass --provider claude once ANTHROPIC_API_KEY access is confirmed.
  - The local mock archive (mock_d360.py) is the default write target,
    since this environment's writes to the real Document360 API are
    blocked regardless of --live. Discovery and assessment reads can
    still be real — only the draft write is always kept local unless
    --live is explicitly passed.
  - Candidate discovery: tag_map.json is checked first — free, instant,
    for a feature area that's already hand-seeded. Anything not found
    there automatically falls through to a live kb_search.py scan
    instead of failing. There is no longer a --discover mode to choose:
    manual tag_map seeding was a hard requirement before a run could
    even start, and a feature_area that didn't exactly match tag_map's
    one seeded key hard-blocked a manual-entry run with LookupError
    (hit 2026-10-29). A feature area never has to be pre-seeded now —
    tag_map is purely an optional, free shortcut for ones that already are.

Stages 6 (verify) and 7 (tag-map learning / run logging) are out of scope
for the MVP — see the file structure notes in DOC_SYNC_README.md.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))  # d360_client.py lives in ../core

import candidates
import draft_writer
import mock_d360
import review_queue
from assess import AssessmentError
from change_note import load_change_note
from d360_client import Document360Client


def run(change_note_path, live=False, provider="gemini", product_line=None,
        only_ids=None, limit=None):
    # Imported here, not at module level, so picking "claude" never
    # requires google-genai to be installed, and vice versa.
    if provider == "gemini":
        from assess_gemini import assess_article
    else:
        from assess import assess_article
        print("(using --provider claude — confirm ANTHROPIC_API_KEY is set)")

    change_note = load_change_note(change_note_path)

    # real_reads: whether article_ids point at the real Document360 KB
    # (needs Document360Client for reads) or the local mock archive
    # (tag_map's seeded ids are mock fixtures, not real article ids).
    if only_ids:
        # Explicit ids bypass discovery entirely — no reason to spend
        # kb_search.py's semantic-triage call re-deriving a candidate list
        # the caller already has (webapp.py's /discover screen already
        # ran it once; re-running it here to immediately throw most of it
        # away was pure waste, and the exact bug that burned two quota
        # calls on nothing on 2026-10-29). Checked against tag_map rather
        # than assumed real, so a confirmed tag_map selection (mock ids)
        # and a live-search selection (real ids) are both handled correctly
        # without the caller having to say which kind it's passing.
        article_ids = list(only_ids)
        print(f"Using {len(article_ids)} explicitly provided article id(s), skipping discovery: {article_ids}")
        tag_map_ids = set(candidates.find_candidates(change_note))
        real_reads = not (tag_map_ids and set(article_ids) <= tag_map_ids)
    else:
        article_ids = candidates.find_candidates(change_note)
        if article_ids:
            print(f"{len(article_ids)} candidate article(s) from tag_map for "
                  f"feature_area={change_note.feature_area!r}: {article_ids}")
            real_reads = False
        else:
            import kb_search
            # --product-line (explicit override) beats the change note's own
            # structured `product_line` field beats kb_search.py's default —
            # a structured note no longer needs a human to separately
            # remember to pass this, which is the same mistake that caused
            # the wrong-workspace bug in the first place.
            kb_product_line = product_line or change_note.product_line or kb_search.DEFAULT_PRODUCT_LINE
            article_ids, found, scanned = kb_search.find_candidates_live(change_note, product_line=kb_product_line)
            print(f"No tag_map entry for feature_area={change_note.feature_area!r} — ran a live KB "
                  f"search under {kb_product_line!r} instead: scanned {len(scanned)} real article(s), "
                  f"found {len(article_ids)} candidate(s):")
            for c in found:
                print(f"    [{c['article_id']}] {c['title']} — {c['reason']}")
            real_reads = True
        if limit is not None:
            article_ids = article_ids[:limit]
            print(f"Limiting this run to the first {limit} candidate(s): {article_ids}")

    # Real ids need the real API for reads regardless of --live — the
    # local mock archive has never heard of them. Only the draft WRITE
    # stays mock-safe (see the per-article mirroring below) unless --live
    # is passed. tag_map ids are mock fixtures by construction.
    read_client = Document360Client() if real_reads else (None if live else mock_d360.MockDocument360Client())
    service = None if live else mock_d360.MockArticleService()

    # Returned so callers other than this CLI (webapp.py) can render the
    # outcome instead of scraping printed text. The prints below stay for
    # terminal use — this is additive, not a replacement.
    results = []

    for article_id in article_ids:
        print(f"\nAssessing {article_id}...")
        # A bad response from either provider, or a write failure on one
        # article, shouldn't abort the rest of the batch — each candidate
        # gets its own outcome, success or failure.
        try:
            assessment = assess_article(article_id, change_note, client=read_client)
        except AssessmentError as exc:
            print(f"  ERROR assessing {article_id}: {exc}")
            results.append({
                "article_id": article_id, "outcome": "error",
                "confidence": None, "rationale": str(exc), "queue_entry": None,
            })
            continue

        if not assessment.needs_edit:
            print(f"  No edit needed (confidence={assessment.confidence}). {assessment.rationale}")
            results.append({
                "article_id": article_id, "outcome": "no_action",
                "confidence": assessment.confidence, "rationale": assessment.rationale,
                "queue_entry": None,
            })
            continue

        print(f"  Flagged (confidence={assessment.confidence}). {assessment.rationale}")

        draft_client = read_client
        if real_reads and not live:
            # Standing decision: no real writes in this environment,
            # regardless of where discovery/assessment read from. Mirror
            # the real article's current content into the local mock
            # archive (idempotent — never overwrites an in-progress mock
            # draft) so the write still goes through the proven mock-safe
            # path, just seeded with real content instead of a
            # hand-written fixture.
            real_article = read_client.get_article(article_id)["data"]
            mock_d360.seed_from_real(article_id, real_article)
            draft_client = mock_d360.MockDocument360Client()

        try:
            entry = draft_writer.handle(article_id, change_note, assessment, client=draft_client, service=service)
        except Exception as exc:
            print(f"  ERROR writing draft for {article_id}: {exc}")
            results.append({
                "article_id": article_id, "outcome": "error",
                "confidence": assessment.confidence, "rationale": str(exc), "queue_entry": None,
            })
            continue

        results.append({
            "article_id": article_id, "outcome": "flagged",
            "confidence": assessment.confidence, "rationale": assessment.rationale,
            "queue_entry": entry,
        })
        if entry is None:
            continue
        print(f"  -> queue item [{entry['id']}] status={entry['status']}")
        if entry.get("verification") and not entry["verification"]["ok"]:
            for warning in entry["verification"]["warnings"]:
                print(f"     ⚠ verification: {warning}")

    return results


def review(action, item_id):
    if action == "list":
        for item in review_queue.list_pending():
            print(f"[{item['id']}] ({item['status']}) article={item['article_id']} "
                  f"feature={item['feature_area']} confidence={item['confidence']}")
            print(f"    {item['rationale']}")
        return

    if not item_id:
        sys.exit("Provide an item id to approve/reject")
    status = "approved" if action == "approve" else "rejected"
    review_queue.mark(item_id, status)
    print(f"{item_id} marked {status}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run a change note through stages 1-4")
    run_p.add_argument("--change-note", required=True, dest="path")
    run_p.add_argument("--live", action="store_true",
                        help="Use the real Document360 API instead of the local mock archive (default: mock)")
    run_p.add_argument("--provider", choices=["claude", "gemini"], default="gemini",
                        help="Model backend for assessment (default: gemini — primary until ANTHROPIC_API_KEY is confirmed)")
    run_p.add_argument("--product-line", default=None,
                        help="The real Document360 workspace to search, by display name, if "
                             "tag_map.json has no entry for this change note's feature_area and a "
                             "live KB search is needed (default: the change note's own product_line "
                             "field, else kb_search.py's DEFAULT_PRODUCT_LINE, currently 'DAP for "
                             "Web'). Each product line is a fully separate workspace with its own "
                             "article set. Ignored when tag_map already has a match.")
    run_p.add_argument("--only", default=None,
                        help="Comma-separated article ids — assess only these from the discovered "
                             "candidates, skipping the rest. For quota-limited live demos.")
    run_p.add_argument("--limit", type=int, default=None,
                        help="Assess only the first N discovered candidates, skipping the rest. "
                             "For quota-limited live demos.")

    review_p = sub.add_parser("review", help="Work the review queue (stage 5)")
    review_p.add_argument("action", choices=["list", "approve", "reject"])
    review_p.add_argument("item_id", nargs="?")

    args = parser.parse_args()
    if args.command == "run":
        only_ids = [a.strip() for a in args.only.split(",")] if args.only else None
        run(args.path, live=args.live, provider=args.provider,
            product_line=args.product_line, only_ids=only_ids, limit=args.limit)
    elif args.command == "review":
        review(args.action, args.item_id)


if __name__ == "__main__":
    main()

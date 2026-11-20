"""The original change-note CLI: run a change note through candidate
lookup, assessment, draft generation and verification, then work the
review queue from the same CLI. Ticket runs (ticket_run.py, the doc-sync
skill) are the main entry point now; this stays for one-off runs on a
change-note file and for the mock archive.

Current defaults, as of this standing decision — not a fallback, the
actual setup until told otherwise:
  - Claude runs triage and assessment, called through `claude -p` on the
    writer's Claude Code login (claude_call.py, assess.py) — no
    ANTHROPIC_API_KEY needed. It is the only model provider: the Gemini
    fallback was removed on 2026-11-15.
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

Tag-map learning (recording confirmed candidates back into tag_map.json)
is not built. See doc_sync/README.md for the whole pipeline.
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


def run(change_note_path, live=False, product_lines=None,
        only_ids=None, limit=None, discovery="titles"):
    """`product_lines` (a list of live workspace names) overrides the change
    note's own product lines as the discovery scope; see
    kb_search.resolve_scope()."""
    from assess import assess_article

    change_note = load_change_note(change_note_path)

    # real_reads: whether article_ids point at the real Document360 KB
    # (needs Document360Client for reads) or the local mock archive
    # (tag_map's seeded ids are mock fixtures, not real article ids).
    if only_ids:
        # Explicit ids bypass discovery entirely — no reason to spend
        # kb_search.py's semantic-triage call re-deriving a candidate list
        # the caller already has (re-running it to immediately throw most
        # of it away burned two quota calls on nothing on 2026-10-29).
        # Checked against tag_map rather
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
            # Scope (2026-11-06): --product-lines (explicit override) beats
            # the change note's own product_lines (a ticket's, required at
            # intake) beats the mode's default — DAP for Web for "titles",
            # all six for "index". The same rule for both modes: the
            # workspaces the writer named are the ones searched.
            mode = discovery if (discovery == "titles" or kb_search.index_available()) else "titles"
            scope = kb_search.resolve_scope(change_note, product_lines, "titles" if mode == "titles" else "index")
            article_ids, found, scanned = kb_search.find_candidates_live(
                change_note, product_lines=product_lines, discovery=discovery,
            )
            print(f"No tag_map entry for feature_area={change_note.feature_area!r} — ran a live KB "
                  f"search ({mode}) in {', '.join(scope)}: scanned "
                  f"{len(scanned)} real article(s), found {len(article_ids)} candidate(s):")
            for c in found:
                print(f"    [{c['article_id']}] {c['title']} ({c.get('workspace') or '?'}) — {c['reason']}")
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

    # Returned so a caller other than this CLI can use the outcome
    # instead of scraping printed text. The prints below stay for
    # terminal use — this is additive, not a replacement.
    results = []

    for article_id in article_ids:
        print(f"\nAssessing {article_id}...")
        # A bad model response, or a write failure on one
        # article, shouldn't abort the rest of the batch — each candidate
        # gets its own outcome, success or failure.
        # Any exception, not just AssessmentError: a failed model call or
        # Document360 read used to abort the whole run,
        # losing every result already gathered.
        try:
            assessment = assess_article(article_id, change_note, client=read_client)
        except Exception as exc:
            print(f"  ERROR assessing {article_id}: {type(exc).__name__}: {exc}")
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
        try:
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
    run_p.add_argument("--product-lines", "--product-line", dest="product_lines", default=None,
                        help="Comma-separated live workspaces to search (e.g. 'DAP for Web, DAP for "
                             "Desktop'), overriding the change note's own product_lines. Default: "
                             "the change note's product lines (a ticket run always has them), else "
                             "'DAP for Web' for --discovery titles and all six for --discovery index. "
                             "Ignored when tag_map already has a match.")
    run_p.add_argument("--discovery", choices=["titles", "index", "both"], default="titles",
                        help="How the live KB search finds candidates when tag_map has no entry. "
                             "'titles' (default): triage every title in each workspace in scope, one "
                             "call per workspace. 'index': search article bodies in scope with the "
                             "local knowledge index (python3 doc_sync/kb_index.py build), then triage "
                             "that shortlist; falls back to 'titles' if no index is built. 'both': "
                             "index plus a strict title check on Haiku, merged (found_by).")
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
        import kb_search
        only_ids = [a.strip() for a in args.only.split(",")] if args.only else None
        run(args.path, live=args.live,
            product_lines=kb_search.parse_product_lines(args.product_lines), only_ids=only_ids,
            limit=args.limit, discovery=args.discovery)
    elif args.command == "review":
        review(args.action, args.item_id)


if __name__ == "__main__":
    main()

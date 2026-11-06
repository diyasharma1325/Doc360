"""Stage 4 (script, safety-enforced): the only file allowed to write to
Document360. Takes an Assessment that says an article needs an edit,
checks whether the article already has an unresolved draft, and either
creates the new draft or flags the article for manual merge instead of
overwriting someone's in-progress work. Never calls publish() — publishing
stays a manual step you or your team do directly in Document360.

The write itself is a fork: a new draft version branched off the live
article, so the published version stays exactly as it was until someone
publishes the draft by hand (see ArticleService.fork_and_update()).

Order is the safety property: the draft-exists check runs on the article
as read BEFORE anything is forked, and a hit stops here with nothing
written. A fork is itself an unpublished draft, so re-running the same
change note finds it and flags a merge instead of forking twice.

The draft-exists check reads `status`, `public_version` and
`latest_version` off get_article() — all confirmed against live
responses on 2026-11-04 (see d360_client.get_article()).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))  # d360_client.py / articles.py live in ../core

from d360_client import Document360Client
from articles import ArticleService
import review_queue
import verify

DRAFT_STATUS = 0  # get_article()'s `status`: 0 = latest version is an unpublished draft, 3 = published


def has_pending_draft(article):
    """True if the article's latest version is not the published one.
    Two independent signals, either of which flags it: `status == 0`, and
    `latest_version > public_version`. They agreed on every live article
    checked, so the second only ever ADDS flags — it is there so a single
    stale or missing field can't make in-progress work look safe to fork
    over. A mock record carrying neither version field falls back to
    `status` alone, exactly as before."""
    if article.get("status") == DRAFT_STATUS:
        return True
    latest, public = article.get("latest_version"), article.get("public_version")
    return latest is not None and public is not None and latest > public


def handle(article_id, change_note, assessment, client=None, service=None):
    if not assessment.needs_edit:
        return None

    client = client or Document360Client()
    service = service or ArticleService(client)

    article = client.get_article(article_id)["data"]

    base_entry = {
        "article_id": article_id,
        "feature_area": change_note.feature_area,
        "rationale": assessment.rationale,
        "confidence": assessment.confidence,
    }

    if not assessment.updated_html_content:
        # The model said it needs an edit but gave us nothing to write —
        # something about its response didn't add up, so a human needs to
        # look rather than the pipeline guessing.
        return review_queue.add({
            **base_entry,
            "status": "merge_conflict",
            "note": "Model reported needs_edit=True but returned no updated_html_content — needs manual review.",
        })

    if has_pending_draft(article):
        return review_queue.add({
            **base_entry,
            "status": "merge_conflict",
            "proposed_html_content": assessment.updated_html_content,
            "note": "Article already has an unpublished draft — merge by hand instead of overwriting it.",
        })

    service.fork_and_update(
        article_id=article_id,
        content=assessment.updated_html_content,
        current=article,
    )

    verification = verify.verify_article(
        article_id, change_note, assessment.original_html_content, client=client
    )

    note = "Draft written — review the latest draft version for this article directly in Document360."
    if not verification.ok:
        note += " Verification found possible issues — see below before approving."

    return review_queue.add({
        **base_entry,
        "status": "pending",
        "note": note,
        "verification": {"ok": verification.ok, "warnings": verification.warnings},
    })

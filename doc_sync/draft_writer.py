"""Stage 4 (script, safety-enforced): the only file allowed to write to
Document360. Takes an Assessment that says an article needs an edit,
checks whether the article already has an unresolved draft, and either
creates the new draft or flags the article for manual merge instead of
overwriting someone's in-progress work. Never calls publish() — publishing
stays a manual step you or your team do directly in Document360.

The draft-exists check reads `article["status"]` off the same response
`d360_client.get_article()` returns. That field name, and `version_number`
below, are carried over from d360_client.py's existing conventions
(STATUS_MAP_ARTICLE in doc360-ia-audit/audit.py maps 0 -> draft, 3 ->
published) but have not been confirmed against a live get_article() call
yet — verify both before trusting this on anything real.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))  # d360_client.py / articles.py live in ../core

from d360_client import Document360Client
from articles import ArticleService
import review_queue
import verify

DRAFT_STATUS = 0  # see STATUS_MAP_ARTICLE in doc360-ia-audit/audit.py


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

    if article.get("status") == DRAFT_STATUS:
        return review_queue.add({
            **base_entry,
            "status": "merge_conflict",
            "proposed_html_content": assessment.updated_html_content,
            "note": "Article already has an unpublished draft — merge by hand instead of overwriting it.",
        })

    version_number = article.get("version_number", 1)
    service.update(
        article_id=article_id,
        content=assessment.updated_html_content,
        version_number=version_number,
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

"""Stage 6 (verify): runs immediately after draft_writer.py writes a
draft — not after human approval, deliberately, so the result is
visible to the human as a confidence signal *before* they decide, not
after. Re-fetches the article and checks a few cheap, high-signal things
rather than attempting full HTML validation: did old wording that was in
the article word for word actually get removed, is the HTML structurally
intact, did the content shrink suspiciously, did an image silently
disappear.
"""
from dataclasses import dataclass, field
from typing import List

from assess import _extract_image_srcs
from d360_client import Document360Client


def _image_path(src):
    """An image URL without its query string or fragment."""
    return src.split("#", 1)[0].split("?", 1)[0]


@dataclass
class VerificationResult:
    ok: bool
    warnings: List[str] = field(default_factory=list)


def _old_texts(change_note):
    """Every `old` wording the change note gives: the per-content-type ones
    when it has a `changes` list, else the single `old`."""
    olds = [c.old for c in (change_note.changes or [])] or [change_note.old]
    return [o.strip() for o in olds if o and o.strip()]


def verify_article(article_id, change_note, before_html, client=None):
    client = client or Document360Client()
    after_html = client.get_article(article_id)["data"].get("html_content", "")

    warnings = []

    # A change note's old/new are usually summary sentences ("Users could
    # not validate domains..."), not text copied from the article, so a
    # literal check fired on nearly every draft (2026-11-06). Now: warn only
    # when an old wording WAS in the article word for word and still is.
    # There is no "new text present" check; an edit rewords to fit the
    # article and can't be expected to contain the note's sentence.
    for old in _old_texts(change_note):
        if old in (before_html or "") and old in after_html:
            warnings.append(f"Old text still present: {old!r}")

    if after_html.count("<") != after_html.count(">"):
        warnings.append("Mismatched '<'/'>' counts — HTML may be malformed or truncated")

    if before_html and len(after_html) < len(before_html) * 0.5:
        warnings.append(f"Content shrank by more than half ({len(before_html)} -> {len(after_html)} chars)")

    # Compared without the query string: Document360 serves image URLs with a
    # time-limited SAS signature (?sv=...&se=...&sig=...) that changes on every
    # read, so a before/after read minutes apart flagged EVERY image as missing
    # (2026-11-11, WSC-900010; all images were present on read-back).
    missing_images = set(map(_image_path, _extract_image_srcs(before_html))) \
        - set(map(_image_path, _extract_image_srcs(after_html)))
    if missing_images:
        warnings.append(f"{len(missing_images)} image(s) missing after the edit: {sorted(missing_images)}")

    return VerificationResult(ok=not warnings, warnings=warnings)

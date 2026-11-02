"""Stage 6 (verify): runs immediately after draft_writer.py writes a
draft — not after human approval, deliberately, so the result is
visible to the human as a confidence signal *before* they decide, not
after. Re-fetches the article and checks a few cheap, high-signal things
rather than attempting full HTML validation: did the old text actually
get removed, did the new text actually land, is the HTML structurally
intact, did an image silently disappear.
"""
from dataclasses import dataclass, field
from typing import List

from assess import _extract_image_srcs
from d360_client import Document360Client


@dataclass
class VerificationResult:
    ok: bool
    warnings: List[str] = field(default_factory=list)


def verify_article(article_id, change_note, before_html, client=None):
    client = client or Document360Client()
    after_html = client.get_article(article_id)["data"].get("html_content", "")

    warnings = []

    if change_note.old and change_note.old in after_html:
        warnings.append(f"Old text still present: {change_note.old!r}")

    if change_note.new and change_note.new not in after_html:
        warnings.append(f"Expected new text not found: {change_note.new!r}")

    if after_html.count("<") != after_html.count(">"):
        warnings.append("Mismatched '<'/'>' counts — HTML may be malformed or truncated")

    if before_html and len(after_html) < len(before_html) * 0.5:
        warnings.append(f"Content shrank by more than half ({len(before_html)} -> {len(after_html)} chars)")

    missing_images = set(_extract_image_srcs(before_html)) - set(_extract_image_srcs(after_html))
    if missing_images:
        warnings.append(f"{len(missing_images)} image(s) missing after the edit: {sorted(missing_images)}")

    return VerificationResult(ok=not warnings, warnings=warnings)

"""Stage 3 (agent), Claude path — the DEFAULT provider: reads one
article's real content against a change note and decides whether it needs
an edit, and if so, what the edit is.

Calls Claude through `claude -p` on the writer's Claude Code login
(claude_call.py), so no ANTHROPIC_API_KEY is needed. assess_gemini.py is the
fallback (`--provider gemini`); it reuses this module's prompt and input
builders, so the two providers are never shown different inputs.
"""
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
sys.path.insert(0, str(REPO_ROOT / "core"))  # d360_client.py lives in ../core

import claude_call
import product_context
from d360_client import Document360Client

MODEL = claude_call.DEFAULT_MODEL
ROOT = THIS_DIR  # assess_prompt.md lives alongside this file

# A flagged article comes back as its FULL corrected html_content, which can
# run tens of KB — the same headroom assess_gemini.py gives it.
MAX_OUTPUT_TOKENS = 32768

MAX_IMAGES = 6  # cap per article on the image-src scan verify.py uses for its missing-image check
IMG_SRC_RE = re.compile(r'<img[^>]+src=["\']([^"\'>]+)["\']', re.IGNORECASE)

ASSESS_SCHEMA = {
    "type": "object",
    "properties": {
        "needs_edit": {"type": "boolean"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "rationale": {"type": "string", "description": "Why, in one or two sentences."},
        "updated_html_content": {
            "type": ["string", "null"],
            "description": "Full corrected html_content. Required if needs_edit is true, otherwise null.",
        },
    },
    "required": ["needs_edit", "confidence", "rationale", "updated_html_content"],
}


class AssessmentError(RuntimeError):
    """Raised when a model's response can't be turned into an Assessment —
    e.g. no tool call came back, or a required field is missing. Shared by
    assess.py and assess_gemini.py so both providers fail the same way."""


@dataclass
class Assessment:
    needs_edit: bool
    confidence: str
    rationale: str
    updated_html_content: Optional[str]
    original_html_content: str = ""


REQUIRED_RESULT_FIELDS = ("needs_edit", "confidence", "rationale", "updated_html_content")


def _assessment_from_result(result, original_html_content):
    missing = [f for f in REQUIRED_RESULT_FIELDS if f not in result]
    if missing:
        raise AssessmentError(f"Model response is missing required field(s) {missing}. Got: {result!r}")
    return Assessment(
        needs_edit=result["needs_edit"],
        confidence=result["confidence"],
        rationale=result["rationale"],
        updated_html_content=result.get("updated_html_content"),
        original_html_content=original_html_content,
    )


def _load_system_prompt(product_line=None):
    parts = [(ROOT / "assess_prompt.md").read_text()]
    for guideline in ("document360-formatting.md", "whatfix-writing-guidelines-agent.md"):
        path = REPO_ROOT / "guidelines" / guideline  # these live in ../guidelines, not here
        if path.exists():
            parts.append(f"\n\n## {guideline}\n\n" + path.read_text())
    # Product context: scoped reference, not a general dump. Selected per
    # product line (2026-11-04) — the article's own workspace, see
    # product_context.py. No product line means DAP for Web's two files
    # (dap-core.md + dap-web.md), the only ones this prompt carried before.
    parts.extend(product_context.prompt_parts(product_line))
    return "\n".join(parts)


def _extract_image_srcs(html_content):
    """Unescaped before comparison — a model that re-serializes html_content
    may write a URL's '&' as '&amp;' (standard HTML attribute encoding, and
    arguably more correct than the original's raw '&'); without unescaping,
    verify.py's before/after set comparison treats the identical image as a
    different URL and flags it as missing. Confirmed real, not theoretical:
    this is exactly what produced a false "6 image(s) missing" warning on a
    real run (2026-10-29) where no image had actually been dropped."""
    seen = []
    for src in IMG_SRC_RE.findall(html_content):
        src = html.unescape(src)
        if src not in seen:
            seen.append(src)
    return seen[:MAX_IMAGES]


def _build_change_note_text(change_note, html_content):
    """Shared by assess.py and assess_gemini.py so both providers see the
    exact same input. Renders the per-type `changes` list (when a change
    note has one) as its own clearly-labeled section instead of cramming
    several content types into one old/new sentence — and lists
    `unaffected_content_types` explicitly so the model doesn't need to
    infer "not mentioned" as "not affected" on its own. Falls back to the
    plain old/new pair for a change note without this structure."""
    lines = [
        "Change note:",
        f"- feature_area: {change_note.feature_area}",
        f"- summary: {change_note.summary}",
        f"- notes: {change_note.notes}",
    ]
    if change_note.effective_date:
        lines.insert(3, f"- effective_date: {change_note.effective_date}")
    if change_note.changes:
        lines.append("\nPer-content-type changes:")
        for c in change_note.changes:
            lines.append(f"  - {c.content_type}: {c.old!r} -> {c.new!r}")
    else:
        lines.append(f"- old: {change_note.old}")
        lines.append(f"- new: {change_note.new}")
    if change_note.unaffected_content_types:
        lines.append(
            "\nExplicitly UNAFFECTED by this change (do not flag an article as "
            "needing this edit just because it covers one of these): "
            + ", ".join(change_note.unaffected_content_types)
        )
    lines.append(f"\nArticle html_content:\n{html_content}")
    return "\n".join(lines)


def assess_article(article_id, change_note, client=None):
    client = client or Document360Client()
    article = client.get_article(article_id)["data"]
    html_content = article.get("html_content", "")

    text = _build_change_note_text(change_note, html_content)

    try:
        result = claude_call.generate(
            system=_load_system_prompt(product_context.product_line_of(article, change_note)),
            user=text,
            schema=ASSESS_SCHEMA,
            label="assess",
            model=MODEL,
            max_tokens=MAX_OUTPUT_TOKENS,
        )
    except claude_call.ClaudeCallError as exc:
        raise AssessmentError(str(exc)) from exc
    return _assessment_from_result(result, html_content)

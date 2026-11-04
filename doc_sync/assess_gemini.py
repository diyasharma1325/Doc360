"""PRIMARY assessment path as of this standing decision — not a
substitute. Uses Gemini (gemini-3.5-flash) and is pipeline.py's default
provider until ANTHROPIC_API_KEY access is confirmed, at which point
assess.py (Claude) becomes default again via --provider claude.

Same interface as assess.py — assess_article(article_id, change_note,
client=None) -> Assessment — and reuses its prompt-loading helper
directly, so the two providers are never shown different inputs.

Confirmed working against a live call (see doc_sync/README.md for the
test record). Retries transient 503s with backoff — observed in
practice to happen even on this "stable" model, back to back with a
successful call, so this isn't a one-off hardening, it's a real
operating condition. gemini-4-argon was tried first and rejected: real
model, confirmed to exist, but returned 429 (free-tier quota is 0 for
it) and then repeated 503s on retry — not viable for a free-tier key.
"""
import time

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

import product_context
from assess import AssessmentError, _assessment_from_result, _build_change_note_text, _load_system_prompt
from d360_client import Document360Client

MODEL = "gemini-3.5-flash"

ASSESS_FUNCTION = types.FunctionDeclaration(
    name="report_assessment",
    description="Report whether the article needs a text edit for this change.",
    parameters={
        "type": "object",
        "properties": {
            "needs_edit": {"type": "boolean"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "rationale": {"type": "string", "description": "Why, in one or two sentences."},
            "updated_html_content": {
                "type": "string",
                "nullable": True,
                "description": "Full corrected html_content. Required if needs_edit is true, otherwise null.",
            },
        },
        "required": ["needs_edit", "confidence", "rationale", "updated_html_content"],
    },
)


def assess_article(article_id, change_note, client=None):
    client = client or Document360Client()
    article = client.get_article(article_id)["data"]
    html_content = article.get("html_content", "")

    parts = [_build_change_note_text(change_note, html_content)]

    gclient = genai.Client()  # reads GEMINI_API_KEY from the environment
    config = types.GenerateContentConfig(
        system_instruction=_load_system_prompt(product_context.product_line_of(article, change_note)),
        # The same failure kb_search.py's triage hit: thinking tokens
        # alone can exhaust a tight budget before any output is written.
        # This call needs even more headroom than that one did — a
        # flagged article returns its FULL corrected html_content, which
        # can run tens of KB, on top of thinking tokens. Bumped again
        # (2026-11-02) when dap-core.md/dap-web.md were added to the
        # system prompt — a bigger, denser prompt gives this model more
        # to reason over before answering, and thinking tokens share this
        # same budget with the final output.
        max_output_tokens=32768,
        thinking_config=types.ThinkingConfig(thinking_budget=3072),
        tools=[types.Tool(function_declarations=[ASSESS_FUNCTION])],
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="ANY",
                allowed_function_names=["report_assessment"],
            )
        ),
    )

    # Observed in practice: this model intermittently returns a transient
    # 503 ("high demand") even back to back with a successful call. Retry
    # a few times with backoff before giving up, rather than letting one
    # hiccup kill the whole run.
    max_attempts = 4
    for attempt in range(1, max_attempts + 1):
        try:
            response = gclient.models.generate_content(model=MODEL, contents=parts, config=config)
            break
        except genai_errors.ServerError as exc:
            if attempt == max_attempts:
                raise
            wait = 5 * attempt
            print(f"    (Gemini call failed with {exc} — retrying in {wait}s, attempt {attempt}/{max_attempts})")
            time.sleep(wait)

    candidates_out = response.candidates or []
    if not candidates_out or not getattr(candidates_out[0].content, "parts", None):
        raise AssessmentError(f"Gemini returned no usable content. response={response!r}")

    function_call = next(
        (p.function_call for p in candidates_out[0].content.parts if getattr(p, "function_call", None)),
        None,
    )
    if function_call is None:
        raise AssessmentError(
            "Gemini did not return the expected function call — it may have answered in plain text instead."
        )

    return _assessment_from_result(dict(function_call.args), html_content)

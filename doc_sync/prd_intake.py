"""Stage 1 (Intake), alternative to hand-typing a change note: extracts a
structured ChangeNote from a PRD (or similar product-change document) via
one model call, instead of a person transcribing it into the five old
fields by hand. Takes plain text/markdown — if your source is a PDF or
slide deck, extract its text first (the `pdf` skill handles this); this
module doesn't parse PDFs itself.

The output still needs a human read-through before it drives the
pipeline. The extraction deliberately leaves `effective_date` and
`product_line` blank rather than guessing when the document doesn't
clearly state them, and `affected_content_types`/
`unaffected_content_types` reflect only what the document actually says
— review the written change note the same way you'd review a hand-typed
one before running `pipeline.py run` against it.
"""
import argparse
import os
import sys
import time
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR.parent / "core"))  # d360_client.py lives in ../core

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

import workspaces
from change_note import ChangeNote, ContentChange, save_change_note
from d360_client import Document360Client

MODEL = "gemini-3.5-flash"
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prd_intake_prompt.md")

CHANGE_NOTE_FUNCTION = types.FunctionDeclaration(
    name="report_change_note",
    description="Report the structured change note extracted from this document.",
    parameters={
        "type": "object",
        "properties": {
            "feature_area": {"type": "string"},
            "summary": {"type": "string"},
            "old": {"type": "string"},
            "new": {"type": "string"},
            "effective_date": {"type": "string", "description": "ISO date, or empty string if not stated."},
            "product_line": {"type": "string", "description": "One of the given real workspace names, or empty string if unclear."},
            "affected_content_types": {"type": "array", "items": {"type": "string"}},
            "unaffected_content_types": {"type": "array", "items": {"type": "string"}},
            "changes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "content_type": {"type": "string"},
                        "old": {"type": "string"},
                        "new": {"type": "string"},
                    },
                    "required": ["content_type", "old", "new"],
                },
            },
            "notes": {"type": "string"},
        },
        "required": [
            "feature_area", "summary", "old", "new", "effective_date", "product_line",
            "affected_content_types", "unaffected_content_types", "changes", "notes",
        ],
    },
)


def _real_product_lines(client=None):
    """The live workspace names a PRD may be routed to: the account's real
    /ProjectVersions list, narrowed to workspaces.LIVE_WORKSPACES so a
    change note can never be pointed at Archived or another non-live
    workspace that discovery would then refuse."""
    client = client or Document360Client()
    versions = client.list_project_versions().get("data", [])
    return [v.get("version_code_name") for v in versions
            if v.get("version_code_name") and workspaces.is_live(v.get("id"))]


def _load_prompt(product_lines):
    template = Path(PROMPT_PATH).read_text()
    return template.replace("{product_lines}", ", ".join(product_lines) or "(none found)")


def extract_change_note(prd_input, client=None, is_pdf=False):
    """One model call: read a PRD and return a ChangeNote. Prefers
    leaving a field blank over guessing — see prd_intake_prompt.md.
    `product_line` is checked against the real workspace list (a live,
    read-only call) and cleared rather than trusted if the model names
    something that doesn't actually exist — the same "search the wrong
    workspace" mistake kb_search.py hit once is not one to risk repeating
    on an unverified model guess.

    `prd_input` is either a plain text/markdown string, or — when
    `is_pdf=True` — the raw bytes of a PDF file. A PDF is sent to Gemini
    as a native document input (the same `Part.from_bytes` mechanism
    assess_gemini.py used for screenshots, just a different mime type),
    not converted to text first: tables and embedded images are read by
    the model as they actually appear, rather than flattened to prose
    before it ever sees them.
    """
    product_lines = _real_product_lines(client)

    gclient = genai.Client()  # reads GEMINI_API_KEY from the environment
    config = types.GenerateContentConfig(
        system_instruction=_load_prompt(product_lines),
        max_output_tokens=8192,
        tools=[types.Tool(function_declarations=[CHANGE_NOTE_FUNCTION])],
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="ANY",
                allowed_function_names=["report_change_note"],
            )
        ),
    )

    contents = (
        [types.Part.from_bytes(data=prd_input, mime_type="application/pdf")]
        if is_pdf else prd_input
    )

    # Same retry behavior as assess_gemini.py/kb_search.py — this model
    # intermittently returns a transient 503 even back to back with a
    # successful call.
    max_attempts = 4
    for attempt in range(1, max_attempts + 1):
        try:
            response = gclient.models.generate_content(model=MODEL, contents=contents, config=config)
            break
        except genai_errors.ServerError as exc:
            if attempt == max_attempts:
                raise
            wait = 5 * attempt
            print(f"    (Gemini call failed with {exc} — retrying in {wait}s, attempt {attempt}/{max_attempts})")
            time.sleep(wait)

    candidates_out = response.candidates or []
    if not candidates_out or not getattr(candidates_out[0].content, "parts", None):
        raise RuntimeError(f"Gemini returned no usable content. response={response!r}")

    function_call = next(
        (p.function_call for p in candidates_out[0].content.parts if getattr(p, "function_call", None)),
        None,
    )
    if function_call is None:
        raise RuntimeError(
            "Gemini did not return the expected function call — it may have answered in plain text instead."
        )

    result = dict(function_call.args)
    if result.get("product_line") and result["product_line"] not in product_lines:
        print(f"    (model proposed product_line={result['product_line']!r}, which isn't a real "
              f"workspace name — clearing it; fill it in by hand before running the pipeline)")
        result["product_line"] = ""

    return ChangeNote(
        feature_area=result["feature_area"],
        summary=result["summary"],
        old=result["old"],
        new=result["new"],
        effective_date=result.get("effective_date", ""),
        notes=result.get("notes", ""),
        product_line=result.get("product_line", ""),
        affected_content_types=list(result.get("affected_content_types") or []),
        unaffected_content_types=list(result.get("unaffected_content_types") or []),
        changes=[ContentChange(**c) for c in result.get("changes") or []],
    )


def main():
    parser = argparse.ArgumentParser(
        description="Extract a structured change note from a PRD — plain text/markdown, or a "
                    "PDF (tables and images are read natively, no text conversion). "
                    "Review the output before running the pipeline against it."
    )
    parser.add_argument("prd_path", help="Path to the PRD — .pdf, or plain text/markdown")
    parser.add_argument("--out", required=True, help="Where to write the resulting change note JSON")
    args = parser.parse_args()

    path = Path(args.prd_path)
    is_pdf = path.suffix.lower() == ".pdf"
    prd_input = path.read_bytes() if is_pdf else path.read_text()

    print(f"Extracting a change note from {args.prd_path}{' (native PDF input)' if is_pdf else ''}...")
    note = extract_change_note(prd_input, is_pdf=is_pdf)
    path = save_change_note(note, args.out)
    print(f"Wrote {path} — review it before running the pipeline, especially effective_date and product_line.")


if __name__ == "__main__":
    main()

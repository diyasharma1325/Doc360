"""Stage 2 (discovery), live alternative to tag_map.py: finds candidate
articles for a change note by walking the real Document360 KB tree
(read-only) and asking the model to semantically triage which article
titles are plausibly affected — catching paraphrased references that a
literal keyword/tag_map lookup would miss.

Semantic triage only, deliberately — an earlier version also ran a
deterministic "keyword floor" (substring match against title/category
path) and included its hits unconditionally alongside the semantic
results. That floor was removed (2026-10-29): it had no context
awareness at all, so any article containing a matched word got listed as
a candidate regardless of whether it was actually about the same
feature — real, observed noise, not a theoretical edge case. The
triage prompt sees the full change note (including the author-reviewed
`affected_content_types`/`unaffected_content_types` lists, when present)
and every article's title and category in one call, which is a strictly
better relevance signal than an incidental substring hit. The trade-off:
there's no longer a zero-cost, can't-fail guarantee underneath it —
discovery now depends entirely on this one model call being thorough.

Read-only end to end — makes no writes, no queue entries, no draft edits.
Uses Gemini (gemini-3.5-flash), matching the pipeline's current primary
provider in assess_gemini.py.
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

from change_note import load_change_note
from d360_client import Document360Client

MODEL = "gemini-3.5-flash"
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "kb_search_prompt.md")

# Document360 splits content into entirely separate project versions
# (workspaces) per product line — DAP for Web, DAP for Desktop, DAP on
# OS, DAP for Mobile, Product Analytics, Archived, etc. — each with its
# own independent category tree. These are NOT folders inside one shared
# KB. `.env`'s D360_PROJECT_ID points at "Archived" (correct for
# draft_writer.py's write-safety sandbox), which is why an earlier
# version of this file that filtered a same-named category folder
# *inside* whatever workspace was configured was silently searching
# Archived's "DAP for Web" subfolder of retired articles, never the real,
# live DAP for Web workspace. `product_line` now resolves to the actual
# workspace via list_project_versions() instead.
DEFAULT_PRODUCT_LINE = "DAP for Web"

CANDIDATES_FUNCTION = types.FunctionDeclaration(
    name="report_candidates",
    description="Report which articles from the list are plausibly affected by this change.",
    parameters={
        "type": "object",
        "properties": {
            "candidates": {
                "type": "array",
                "description": "Articles that plausibly need review for this change. Empty if none.",
                "items": {
                    "type": "object",
                    "properties": {
                        "article_id": {"type": "string"},
                        "title": {"type": "string"},
                        "reason": {
                            "type": "string",
                            "description": "Why this article is plausibly affected, in one short phrase.",
                        },
                    },
                    "required": ["article_id", "title", "reason"],
                },
            },
        },
        "required": ["candidates"],
    },
)


def _load_prompt():
    with open(PROMPT_PATH) as f:
        parts = [f.read()]
    # Product context (2026-11-02), same files and same reasoning as
    # assess.py's _load_system_prompt(): dap-core.md is the shared DAP
    # concept model, dap-web.md the Web-specific delta. Hardcoded to these
    # two until a second product line's delta file exists — see assess.py
    # for the TODO to select by product_line instead. This is a test,
    # not a settled default: this prompt already carries every article
    # title in the workspace (the largest prompt in the pipeline, and the
    # one that already hit a real MAX_TOKENS failure once from size alone
    # — see the thinking_budget note in triage() below), so adding more
    # context here is a real cost, not a free improvement to assume works.
    for product_doc in ("dap-core.md", "dap-web.md"):
        path = THIS_DIR / product_doc
        if path.exists():
            parts.append(f"\n\n## {product_doc}\n\n" + path.read_text())
    return "\n".join(parts)


def _resolve_project_version_id(client, product_line):
    """Look up a Document360 workspace's id by its display name (e.g.
    "DAP for Web"), via the same ProjectVersions list discover.py uses.
    Case-insensitive, whitespace-trimmed."""
    versions = client.list_project_versions().get("data", [])
    target = product_line.strip().lower()
    for v in versions:
        if (v.get("version_code_name") or "").strip().lower() == target:
            return v["id"]
    available = [v.get("version_code_name") for v in versions]
    raise ValueError(
        f"No Document360 workspace named {product_line!r}. Available workspaces: {available}"
    )


def fetch_kb_articles(client=None, project_version_id=None, product_line=DEFAULT_PRODUCT_LINE):
    """Walk a real Document360 workspace's category tree and flatten it
    into one row per article: {id, title, category_path, status}.
    Read-only — mirrors doc360-ia-audit/audit.py's walk().

    Pass `project_version_id` directly to target a workspace by id, or
    `product_line` (its display name, e.g. "DAP for Web") to resolve it
    by name. If both are given, `project_version_id` wins.
    """
    client = client or Document360Client()
    if project_version_id is None:
        if not product_line:
            raise ValueError("Pass either project_version_id or product_line")
        project_version_id = _resolve_project_version_id(client, product_line)
    tree = client.list_categories(
        project_version_id,
        params={"excludeArticles": "false", "includeCategoryDescription": "false"},
    )
    articles = []

    def walk(categories, path):
        for cat in categories or []:
            cat_path = path + [cat.get("name") or "(untitled category)"]
            for art in cat.get("articles") or []:
                articles.append({
                    "id": art.get("id"),
                    "title": art.get("title") or "(untitled article)",
                    "category_path": " > ".join(cat_path),
                    "status": art.get("status"),
                })
            walk(cat.get("child_categories"), cat_path)

    walk(tree.get("data"), [])
    return articles


def triage(change_note, articles):
    """One model call: given the full article list (titles only — no
    content fetched yet), ask which are plausibly affected. Returns the
    list of {article_id, title, reason} dicts the model reported."""
    listing = "\n".join(
        f"- [{a['id']}] {a['title']} ({a['category_path']})" for a in articles
    )
    note_lines = [
        "Change note:",
        f"- feature_area: {change_note.feature_area}",
        f"- summary: {change_note.summary}",
        f"- notes: {change_note.notes}",
    ]
    if change_note.changes:
        note_lines.append("Per-content-type changes:")
        for c in change_note.changes:
            note_lines.append(f"  - {c.content_type}: {c.old!r} -> {c.new!r}")
    else:
        note_lines.append(f"- old: {change_note.old}")
        note_lines.append(f"- new: {change_note.new}")
    if change_note.affected_content_types:
        # The only remaining consumer of this field now that the keyword
        # floor is gone — an explicit, author-reviewed scope list is a
        # strong signal worth giving the model directly rather than
        # letting it re-derive scope from old/new/summary alone.
        note_lines.append(
            "Affected content types (the author explicitly scoped this change to these): "
            + ", ".join(change_note.affected_content_types)
        )
    if change_note.unaffected_content_types:
        note_lines.append(
            "Explicitly UNAFFECTED (do not select an article just for covering one "
            "of these): " + ", ".join(change_note.unaffected_content_types)
        )
    prompt = "\n".join(note_lines) + f"\n\nKnowledge base articles ({len(articles)} total):\n{listing}"

    gclient = genai.Client()  # reads GEMINI_API_KEY from the environment
    config = types.GenerateContentConfig(
        system_instruction=_load_prompt(),
        # A real KB's title listing is large (734 articles ~= 40k prompt
        # tokens in the first live test) and this model spends thousands
        # of tokens "thinking" before answering — left at the assess.py
        # default of 4096 total, thinking alone exhausted the budget
        # before any function call was produced. Capping thinking and
        # raising the ceiling fixed it; see README.md's "Live KB search"
        # section for the full test record. Bumped again (2026-11-02)
        # now that dap-core.md/dap-web.md are also in this prompt — this
        # was already the largest, riskiest prompt in the pipeline for
        # this exact failure mode, so the added context gets a bigger
        # thinking allowance, not the same one stretched further.
        max_output_tokens=16384,
        thinking_config=types.ThinkingConfig(thinking_budget=2048),
        tools=[types.Tool(function_declarations=[CANDIDATES_FUNCTION])],
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="ANY",
                allowed_function_names=["report_candidates"],
            )
        ),
    )

    # Same retry behavior as assess_gemini.py — this model intermittently
    # returns a transient 503 even back to back with a successful call.
    max_attempts = 4
    for attempt in range(1, max_attempts + 1):
        try:
            response = gclient.models.generate_content(model=MODEL, contents=prompt, config=config)
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

    return list(dict(function_call.args).get("candidates", []))


def find_candidates_live(change_note, client=None, project_version_id=None,
                          product_line=DEFAULT_PRODUCT_LINE):
    """Discovery entry point used by pipeline.py's automatic KB fallback:
    walk the real `product_line` workspace, then semantically triage it
    (one model call — see module docstring for why this is the only
    discovery pass now). Returns
    (article_ids, full_candidate_records, all_articles_scanned)."""
    articles = fetch_kb_articles(client, project_version_id, product_line=product_line)
    found = triage(change_note, articles)
    return [c["article_id"] for c in found], found, articles


def main():
    parser = argparse.ArgumentParser(
        description="Test run: search the real Document360 KB for articles affected by a change note. Read-only, makes no writes."
    )
    parser.add_argument("change_note_path")
    parser.add_argument("--product-line", default=DEFAULT_PRODUCT_LINE,
                         help=f"The real Document360 workspace to search, by display name "
                              f"(default: {DEFAULT_PRODUCT_LINE!r}). Each product line is a "
                              f"fully separate workspace with its own article set.")
    args = parser.parse_args()
    product_line = args.product_line

    change_note = load_change_note(args.change_note_path)

    print(f"Walking the real Document360 {product_line!r} workspace (read-only)...")
    t0 = time.time()
    articles = fetch_kb_articles(product_line=product_line)
    t1 = time.time()
    print(f"  {len(articles)} article(s) found in {t1 - t0:.1f}s.")

    print("Running semantic triage against the change note...")
    found = triage(change_note, articles)
    t2 = time.time()
    print(f"  Triage took {t2 - t1:.1f}s. Total: {t2 - t0:.1f}s.\n")

    if not found:
        print("No candidate articles found.")
        return

    print(f"{len(found)} candidate article(s):")
    for c in found:
        print(f"  [{c['article_id']}] {c['title']}")
        print(f"      {c['reason']}")


if __name__ == "__main__":
    main()

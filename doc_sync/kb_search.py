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

Two discovery modes (`discovery=`), "titles" being the default:

- "titles": the original behavior above — every title in ONE workspace,
  one triage call. Unchanged, prompt and all.
- "index" (opt-in, 2026-11-04): a local full-text search of article
  BODIES across all six live workspaces (kb_index.py) picks a shortlist,
  balanced per workspace, and only that shortlist goes to the same
  triage call, each entry with its workspace and the matching excerpt.
  This is not the removed keyword floor coming back: its hits are never
  included unconditionally, they are candidates the model still has to
  accept. What it fixes is the floor's opposite problem — an article
  whose TITLE doesn't name the feature was invisible to "titles" mode
  however good the triage — and it does so with a prompt a fraction of
  the size, even at six times the scope. Falls back to "titles" when no
  index has been built.

Read-only end to end — makes no writes, no queue entries, no draft edits.
The triage call goes to Claude through `claude -p` by default
(claude_call.py), or to Gemini (gemini-3.5-flash) with provider="gemini" —
the same choice as the pipeline's --provider.
"""
import argparse
import os
import re
import sys
import time
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR.parent / "core"))  # d360_client.py lives in ../core

import claude_call
import kb_index
import product_context
import workspaces
from change_note import load_change_note
from d360_client import Document360Client

GEMINI_MODEL = "gemini-3.5-flash"
# Same output ceiling for both providers. Gemini's thinking tokens share it,
# which is what once produced a MAX_TOKENS failure here (see triage()).
TRIAGE_MAX_OUTPUT_TOKENS = 16384
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "kb_search_prompt.md")

DISCOVERY_MODES = ("titles", "index")
DEFAULT_DISCOVERY = "titles"

# "index" mode shortlist sizing. Searched per workspace and capped there
# first, so DAP for Web (half the corpus) can't crowd the others out of
# the list; then merged best-first and capped again so the triage prompt
# stays small (~40 short entries, versus ~1,400 titles in "titles" mode).
INDEX_PER_WORKSPACE = 12
INDEX_SHORTLIST_MAX = 40
INDEX_STALE_AFTER_HOURS = 48
# A feature name found in this many articles or fewer ("display name": 28)
# is specific enough that every article mentioning it goes on the
# shortlist, whatever workspace it's in. Above it ("smart tips": 315) the
# name is too common to say anything on its own, and the per-workspace
# search decides as usual. Kept below INDEX_SHORTLIST_MAX so other matches
# always get some slots.
INDEX_RARE_FEATURE_MAX = 30
# Index-mode triage carries the product reference files for the workspaces
# searched only up to this size (see _load_prompt). Web + Desktop: 65 KB;
# all four DAP surfaces: 102 KB; all six: 177 KB.
INDEX_PRODUCT_CONTEXT_MAX_BYTES = 90_000

# Prepended to the triage request in "index" mode only. kb_search_prompt.md
# describes a full title list, which a shortlist isn't — saying so here,
# rather than editing that file, keeps "titles" mode's prompt unchanged.
_SHORTLIST_NOTE = (
    "Note: the list below is NOT every article. It is a shortlist chosen by a "
    "keyword search over article bodies across several product workspaces, so "
    "each entry also shows its workspace and the passage that matched. Keyword "
    "matches can be incidental: select an article only if it actually documents "
    "the feature or workflow this change note describes, judged by its title, "
    "category and excerpt together.\n\n"
)

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
# workspace via core/workspaces.py's allow-list of the six live product
# workspaces, which also refuses anything outside them (Archived included).
DEFAULT_PRODUCT_LINE = "DAP for Web"

# One schema for both providers: Claude gets it as --json-schema, Gemini as
# the parameters of its forced `report_candidates` function call.
CANDIDATES_SCHEMA = {
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
}


def _load_prompt(product_lines=None, include_products=True):
    """kb_search_prompt.md plus, when `include_products`, the reference
    files for `product_lines` (a list; None or [] means DAP for Web's)."""
    with open(PROMPT_PATH) as f:
        parts = [f.read()]
    # Product context (2026-11-02), same files and same reasoning as
    # assess.py's _load_system_prompt(), selected by product line since
    # 2026-11-04 (product_context.py): "titles" mode gets the files for the
    # one workspace it walked, so DAP for Web — the default — is unchanged.
    # This is a test, not a settled default: this prompt already carries
    # every article title in the workspace (the largest prompt in the
    # pipeline, and the one that already hit a real MAX_TOKENS failure once
    # from size alone — see the thinking_budget note in triage() below), so
    # adding more context here is a real cost, not a free improvement to
    # assume works.
    #
    # "index" mode loads the files for the workspaces it searched only when
    # they total INDEX_PRODUCT_CONTEXT_MAX_BYTES or less (2026-11-06). All six
    # total ~175 KB, which would put back the prompt size the shortlist exists
    # to cut; a ticket scoped to one or two product lines (Web + Desktop is
    # 65 KB) fits, and gets the same grounding "titles" mode has.
    if include_products:
        parts.extend(product_context.prompt_parts_for_lines(product_lines))
    return "\n".join(parts)


def _index_product_lines(names):
    """The product lines whose reference files index-mode triage loads:
    `names` if their files fit INDEX_PRODUCT_CONTEXT_MAX_BYTES, else none."""
    size = product_context.size_of(product_context.files_for_lines(names))
    if size <= INDEX_PRODUCT_CONTEXT_MAX_BYTES:
        return list(names)
    print(f"    (index triage: product reference for {len(names)} workspace(s) is {size // 1000} KB, over "
          f"{INDEX_PRODUCT_CONTEXT_MAX_BYTES // 1000} KB — triaging on the excerpts alone)")
    return None


def _resolve_project_version_id(product_line):
    """Look up a live Document360 workspace's id by its display name (e.g.
    "DAP for Web"). Case-insensitive, whitespace-trimmed. Resolved against
    workspaces.LIVE_WORKSPACES rather than the live /ProjectVersions list,
    so a real-but-not-live workspace ("Archived") is refused by name
    instead of being searched."""
    version_id = workspaces.id_for_name(product_line)
    if version_id is None:
        raise ValueError(
            f"{product_line!r} is not a live Document360 workspace. "
            f"Live workspaces: {workspaces.names()}"
        )
    return version_id


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
        project_version_id = _resolve_project_version_id(product_line)
    workspaces.require_live(project_version_id, "search")
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


def _listing_line(a):
    """`[id] title (category path)` — the "titles" mode format, byte for
    byte. A shortlist entry from "index" mode also carries `workspace` and
    `snippet`, which are added only when present."""
    path = a["category_path"]
    if a.get("workspace"):
        path = f"{a['workspace']} > {path}"
    line = f"- [{a['id']}] {a['title']} ({path})"
    if a.get("snippet"):
        line += "\n    excerpt: " + " ".join(a["snippet"].split())
    return line


def triage(change_note, articles, shortlist=False, product_lines=None, include_products=True,
           provider=claude_call.DEFAULT_PROVIDER, label="triage"):
    """One model call: given the full article list (titles only — no
    content fetched yet), ask which are plausibly affected. Returns the
    list of {article_id, title, reason} dicts the model reported.
    `shortlist=True` marks `articles` as an "index" mode shortlist rather
    than a whole workspace (see _SHORTLIST_NOTE). `product_lines` picks the
    product reference files (default DAP for Web's); `include_products=False`
    leaves them out. `provider` is "claude" (default, claude -p) or
    "gemini" (fallback); both get the same system prompt, request and
    schema. `label` names the call in the token report."""
    listing = "\n".join(_listing_line(a) for a in articles)
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
    if shortlist:
        prompt = _SHORTLIST_NOTE + prompt
    system = _load_prompt(product_lines, include_products=include_products)

    if provider == "claude":
        result = claude_call.generate(
            system=system, user=prompt, schema=CANDIDATES_SCHEMA, label=label,
            max_tokens=TRIAGE_MAX_OUTPUT_TOKENS,
        )
        return list(result.get("candidates", []))
    if provider != "gemini":
        raise ValueError(f"provider must be one of {claude_call.PROVIDERS}, got {provider!r}")
    return _triage_gemini(system, prompt, label)


def _triage_gemini(system, prompt, label="triage"):
    """The Gemini fallback for triage(), unchanged from when Gemini was the
    only provider. Imported lazily, so the Claude path never needs
    google-genai installed."""
    from google import genai
    from google.genai import types

    import gemini_call

    candidates_function = types.FunctionDeclaration(
        name="report_candidates",
        description="Report which articles from the list are plausibly affected by this change.",
        parameters=CANDIDATES_SCHEMA,
    )
    gclient = genai.Client()  # reads GEMINI_API_KEY from the environment
    config = types.GenerateContentConfig(
        system_instruction=system,
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
        max_output_tokens=TRIAGE_MAX_OUTPUT_TOKENS,
        thinking_config=types.ThinkingConfig(thinking_budget=2048),
        tools=[types.Tool(function_declarations=[candidates_function])],
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="ANY",
                allowed_function_names=["report_candidates"],
            )
        ),
    )

    response = gemini_call.generate(gclient, GEMINI_MODEL, prompt, config, label)

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


def _index_query(change_note):
    """The text "index" mode searches with: what the articles that are now
    WRONG would say. So the feature area, summary, the old wording (per
    content type when the note has a `changes` list) and the author's
    affected-content-types list. Deliberately left out: `new` (a stale
    article doesn't contain the new wording yet), and `notes` plus
    `unaffected_content_types` — exclusion language like "Pop-ups did NOT
    move" is exactly what once mined wrong keywords into discovery."""
    parts = [change_note.feature_area, change_note.summary]
    if change_note.changes:
        for c in change_note.changes:
            parts.extend([c.content_type, c.old])
    else:
        parts.append(change_note.old)
    parts.extend(change_note.affected_content_types or [])
    return " ".join(p for p in parts if p)


def _index_focus(change_note):
    """The feature names "index" mode requires a match on: the affected
    content types, each change's content type, and the feature area with
    its slug dashes turned to spaces ("branching-visual-indicators" ->
    "branching visual indicators"). See kb_index.search()'s `focus`."""
    names = list(change_note.affected_content_types or [])
    names.extend(c.content_type for c in (change_note.changes or []))
    names.append(re.sub(r"[-_]+", " ", change_note.feature_area or ""))
    return [n for n in names if n and n.strip()]


def index_available(db_path=kb_index.DEFAULT_DB_PATH):
    st = kb_index.status(db_path)
    return st.get("exists", False) and "error" not in st


def resolve_scope(change_note, product_lines=None, discovery=DEFAULT_DISCOVERY):
    """The live workspaces discovery searches, by display name, in the
    allow-list's spelling: `product_lines` (an explicit override, e.g.
    --product-lines) if given, else the change note's own `product_lines`
    (a ticket's, required at intake), else the mode's default: DAP for Web
    for "titles", all six for "index". Raises ValueError on a name that is
    not a live workspace."""
    names = list(product_lines or getattr(change_note, "product_lines", None) or [])
    if not names:
        return [DEFAULT_PRODUCT_LINE] if discovery == "titles" else workspaces.names()
    out = []
    for name in names:
        version_id = workspaces.id_for_name(name)
        if version_id is None:
            raise ValueError(f"{name!r} is not a live Document360 workspace. Live workspaces: {workspaces.names()}")
        if workspaces.LIVE_WORKSPACES[version_id] not in out:
            out.append(workspaces.LIVE_WORKSPACES[version_id])
    return out


def find_candidates_indexed(change_note, scope=None, db_path=kb_index.DEFAULT_DB_PATH,
                            provider=claude_call.DEFAULT_PROVIDER):
    """"index" mode: full-text search across the workspaces in `scope` (a
    list of live workspace names; None means all six), balanced per
    workspace, then one triage call over the shortlist. Same return shape as
    find_candidates_live(): (article_ids, candidate_records, shortlist)."""
    names = resolve_scope(change_note, scope, discovery="index") if scope else workspaces.names()
    st = kb_index.status(db_path)
    if st.get("age_hours", 0) > INDEX_STALE_AFTER_HOURS:
        print(f"    (knowledge index is {st['age_hours']:.0f}h old, built {st['built_at']}; "
              f"rebuild with: python3 doc_sync/kb_index.py build)")

    query = _index_query(change_note)
    focus = _index_focus(change_note)

    def run(focus):
        hits = []
        for name in names:
            hits.extend(kb_index.search(query, k=INDEX_PER_WORKSPACE, workspace=name, db_path=db_path, focus=focus))
        return hits

    hits = run(focus)
    if not hits:
        # The feature names matched nothing anywhere (a vague or new
        # feature area, no content types listed): search on the whole
        # note's wording instead of returning an empty shortlist.
        print(f"    (no indexed article mentions {focus!r} — searching on the change note's full wording instead)")
        hits = run(None)
    hits.sort(key=lambda h: h["score"])  # bm25: lower is better, comparable across workspaces (one index)

    # Every article that names a rare feature goes first. The 12-per-
    # workspace cap exists so DAP for Web can't crowd the others out, but
    # it also cut 20 of the 26 DAP for Web articles that mention "display
    # name" while other workspaces filled their slots with weak matches
    # (2026-11-06). Applying this only to RARE names leaves cross-product
    # changes, whose name is common or matches nothing, as they were.
    # Counted and searched within the same scope as the rest.
    feature = re.sub(r"[-_]+", " ", change_note.feature_area or "").strip()
    if feature and 0 < kb_index.phrase_count(feature, names, db_path) <= INDEX_RARE_FEATURE_MAX:
        direct = kb_index.search(query, k=INDEX_RARE_FEATURE_MAX, workspace=names, db_path=db_path, focus=[feature])
        direct_ids = {h["article_id"] for h in direct}
        hits = direct + [h for h in hits if h["article_id"] not in direct_ids]
    shortlist = [{
        "id": h["article_id"],
        "title": h["title"],
        "category_path": h["category_path"],
        "workspace": h["workspace"],
        "version_id": h["version_id"],
        "snippet": h["snippet"],
    } for h in hits[:INDEX_SHORTLIST_MAX]]
    if not shortlist:
        return [], [], []

    product_lines = _index_product_lines(names)
    found = triage(change_note, shortlist, shortlist=True, product_lines=product_lines,
                   include_products=product_lines is not None, provider=provider)
    kept = _with_workspace(_only_shown(found, shortlist), shortlist)
    return [c["article_id"] for c in kept], kept, shortlist


def find_candidates_titles(change_note, scope, client=None, provider=claude_call.DEFAULT_PROVIDER):
    """"titles" mode: for EACH workspace in `scope`, walk its full title
    list and triage it in its own call, with that workspace's product
    reference files. One call per workspace, not one merged listing: DAP
    for Web alone is ~1,400 titles (~112k prompt tokens), and a merged
    listing would grow past what has been tested, while giving every
    workspace's titles one product's context. Same return shape as
    find_candidates_live()."""
    client = client or Document360Client()
    all_articles, found = [], []
    for name in scope:
        articles = fetch_kb_articles(client, product_line=name)
        for a in articles:
            a["workspace"] = name
        print(f"    ({name}: {len(articles)} article title(s) to triage)", flush=True)
        label = "triage" if len(scope) == 1 else f"triage {name}"
        picked = _only_shown(triage(change_note, articles, product_lines=[name], provider=provider,
                                    label=label), articles)
        found.extend(_with_workspace(picked, articles))
        all_articles.extend(articles)
    return [c["article_id"] for c in found], found, all_articles


def _only_shown(found, shown_articles):
    """The model may only pick from what it was shown: an id outside the
    list is a hallucination or a typo, never a real candidate. Applied to
    both discovery modes (title mode had no such check before 2026-11-06)."""
    shown = {a["id"] for a in shown_articles}
    kept = [c for c in found if c.get("article_id") in shown]
    if len(kept) < len(found):
        dropped = [c.get("article_id") for c in found if c.get("article_id") not in shown]
        print(f"    (dropped {len(dropped)} candidate(s) whose id wasn't in the list shown: {dropped})")
    return kept


def _with_workspace(found, shown_articles):
    """Each candidate record with the workspace it came from, read off the
    list it was picked from (never the model's word)."""
    workspace_of = {a["id"]: a.get("workspace") for a in shown_articles}
    return [{**c, "workspace": workspace_of.get(c["article_id"])} for c in found]


def find_candidates_live(change_note, client=None, product_lines=None, discovery=DEFAULT_DISCOVERY,
                         provider=claude_call.DEFAULT_PROVIDER):
    """Discovery entry point used by pipeline.py's automatic KB fallback.
    Returns (article_ids, full_candidate_records, all_articles_scanned);
    each candidate record carries its `workspace`.

    The SCOPE is the same rule for both modes (resolve_scope): the
    `product_lines` override, else the change note's own product lines,
    else the mode's default (DAP for Web for "titles", all six for "index").

    discovery="titles": each workspace in scope walked and triaged in its
    own call. discovery="index": the local knowledge index searched within
    scope, then one triage call over the shortlist; falls back to "titles"
    when no index has been built. `provider` picks the triage model:
    "claude" (default) or "gemini"."""
    if discovery not in DISCOVERY_MODES:
        raise ValueError(f"discovery must be one of {DISCOVERY_MODES}, got {discovery!r}")
    if discovery == "index":
        if index_available():
            return find_candidates_indexed(change_note, scope=resolve_scope(change_note, product_lines, "index"),
                                           provider=provider)
        print("    (no knowledge index built yet — falling back to title-only discovery; "
              "build one with: python3 doc_sync/kb_index.py build)")
    scope = resolve_scope(change_note, product_lines, "titles")
    return find_candidates_titles(change_note, scope, client=client, provider=provider)


def parse_product_lines(text):
    """"DAP for Web, DAP for Desktop" -> ["DAP for Web", "DAP for Desktop"];
    None or blank -> None. Names are checked later, by resolve_scope()."""
    names = [n.strip() for n in (text or "").split(",") if n.strip()]
    return names or None


def main():
    parser = argparse.ArgumentParser(
        description="Test run: search the real Document360 KB for articles affected by a change note. Read-only, makes no writes."
    )
    parser.add_argument("change_note_path")
    parser.add_argument("--product-lines", "--product-line", dest="product_lines", default=None,
                         help="Comma-separated live workspaces to search, overriding the change note's "
                              "own product_lines. Default: the change note's product lines, else "
                              f"{DEFAULT_PRODUCT_LINE!r} for 'titles' and all six for 'index'.")
    parser.add_argument("--discovery", choices=DISCOVERY_MODES, default=DEFAULT_DISCOVERY,
                         help="'titles' (default): triage every title in each workspace in scope, one "
                              "call per workspace. 'index': search article bodies in scope with the "
                              "local knowledge index, then triage that shortlist.")
    parser.add_argument("--provider", choices=claude_call.PROVIDERS, default=claude_call.DEFAULT_PROVIDER,
                         help="Model for the triage call: 'claude' (default, claude -p on your Claude "
                              "Code login) or 'gemini' (fallback, needs GEMINI_API_KEY).")
    args = parser.parse_args()

    change_note = load_change_note(args.change_note_path)
    override = parse_product_lines(args.product_lines)
    mode = args.discovery if (args.discovery == "titles" or index_available()) else "titles"
    scope = resolve_scope(change_note, override, mode)
    print(f"Discovery: {mode}, scope: {', '.join(scope)}")

    t0 = time.time()
    _, found, scanned = find_candidates_live(change_note, product_lines=override, discovery=args.discovery,
                                             provider=args.provider)
    print(f"  {'Shortlisted' if mode == 'index' else 'Scanned'} {len(scanned)} article(s). "
          f"Total: {time.time() - t0:.1f}s.\n")

    if not found:
        print("No candidate articles found.")
        return

    print(f"{len(found)} candidate article(s):")
    for c in found:
        print(f"  [{c['article_id']}] {c['title']}  ({c.get('workspace') or '?'})")
        print(f"      {c['reason']}")


if __name__ == "__main__":
    main()

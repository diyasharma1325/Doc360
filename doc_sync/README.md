# Doc Sync Pipeline — MVP

Stages 1-5 of the pipeline sketched in the "Doc Sync Pipeline" artifact,
wired end to end on a narrow slice: one hand-picked change note, a
hand-seeded set of candidate articles, an agent assessment, a
safety-checked draft write, and a review queue. Stages 6 (verify) and 7
(tag-map learning / run logging) are deliberately out of scope for this
MVP.

**Standing decision, current as of this doc** — not a stopgap:
- **Gemini is the primary provider** (`assess_gemini.py`, `gemini-3.5-flash`),
  the default for `pipeline.py run`. Claude (`assess.py`) remains built and
  available via `--provider claude`, and becomes default again once
  `ANTHROPIC_API_KEY` access is confirmed.
- **The local mock archive is the default target** (`mock_d360.py`), since
  live Document360 API access still isn't available in this environment.
  `--live` switches to the real API once that changes.

## Files

| File | Stage | Role |
|---|---|---|
| `change_note.py` | 1 | Defines and validates the change-note shape |
| `tag_map.py` | 2 (state) | Optional feature-area -> article-id cache, hand-seeded; never required |
| `candidates.py` | 2 | Looks up candidates from the tag map (fuzzy-match fallback on `feature_area` typos); returns `[]`, not an error, when there's no confident match, so `pipeline.py` can fall back to a live search |
| `kb_search.py` | 2 | Live search: walks a real Document360 workspace and semantically triages titles against the change note (one model call, no keyword matching). `pipeline.py` runs this automatically whenever `candidates.py` finds no tag_map entry — see "Live KB search" below |
| `kb_search_prompt.md` | 2 (experimental) | Fixed task instructions for `kb_search.py`'s triage call |
| `assess.py` | 3 | Claude path — needs `ANTHROPIC_API_KEY`, not currently default |
| `assess_gemini.py` | 3 | **Gemini path — current default**, needs `GEMINI_API_KEY` |
| `assess_prompt.md` | 3 | Fixed task instructions, concatenated at runtime with `guidelines/document360-formatting.md` and `guidelines/whatfix-writing-guidelines-agent.md`; shared by both assess modules |
| `draft_writer.py` | 4 | Only file that writes to Document360; checks draft status first, never publishes |
| `review_queue.py` | 5 | JSON-backed pending/approved/rejected/merge_conflict queue |
| `mock_d360.py` | — | Local file-backed stand-in for Document360; current default target |
| `pipeline.py` | orchestrator | `run` and `review` CLI commands |

## Setup

```
pip install -r requirements.txt
```

Requires everything already in `.env` (`D360_API_KEY`, `D360_PROJECT_ID`,
`D360_FOLDER_ID`, `D360_USER_ID`) plus `GEMINI_API_KEY` (currently
required — it's the default provider). `ANTHROPIC_API_KEY` is only
needed if you explicitly pass `--provider claude`.

All commands below assume you're running from the repo root (`Doc360/`),
same as `core/cli.py` and `core/discover.py` — `doc_sync/assess.py` and
`doc_sync/draft_writer.py` add `core/` to `sys.path` themselves, so
this works regardless of where you invoke it from.

## Before your first run

1. **Write a real change note**:
   ```
   python3 doc_sync/change_note.py new --out doc_sync/data/changes/my_change.json
   ```
   then edit it in. No tag_map seeding needed first — `pipeline.py` checks
   tag_map.json for a cached mapping and automatically falls back to a
   live KB search (`kb_search.py`) when there isn't one. (Seeding tag_map
   is still worth doing for a feature area you'll re-run often, purely as
   a free shortcut that skips the live search's one model call — see
   `python3 doc_sync/tag_map.py seed --feature "..." --articles "<id1>,<id2>"`.
   It's optional, not a prerequisite: a feature_area that doesn't exactly
   match a seeded key used to hard-fail the run with `LookupError`
   (hit 2026-10-29) — it no longer does.)
2. **Verify the three assumptions flagged in the code** before trusting
   the draft-safety check on anything real (see "Open assumptions" below).

## Running it

```
python3 doc_sync/pipeline.py run --change-note doc_sync/data/changes/my_change.json
python3 doc_sync/pipeline.py review list
python3 doc_sync/pipeline.py review approve <item_id>
python3 doc_sync/pipeline.py review reject <item_id>
```

The `run` command above defaults to `--provider gemini` against the mock
archive — add `--live` once real Document360 access is available, and
`--provider claude` once `ANTHROPIC_API_KEY` is confirmed.

`review approve`/`reject` only updates the queue's own record — it does
not call Document360 again. Publishing a written draft, and discarding a
rejected one, both stay manual actions you take directly in Document360.

## Open assumptions — verify before a real run

These are inferred from `articles.py`'s existing PUT path and
`doc360-ia-audit/audit.py`'s status map, not confirmed against a live
`get_article()` response yet:

- `d360_client.get_article()`'s path (`/Articles/{article_id}/{lang_code}`)
  actually returns the article.
- The response includes a `status` field where `0` means "draft" —
  this is what `draft_writer.py` uses to decide whether to flag an
  article for manual merge instead of writing over it.
- The response includes a `version_number` field that
  `ArticleService.update()` expects back unchanged.

Recommend confirming these with a one-off read-only call (in the spirit
of `discover.py`) against a single test article before running the
pipeline against anything real.

## Live KB search (automatic fallback, no flag to pick it)

`tag_map.py` is an optional cache, not a requirement — `candidates.py`
returns `[]` instead of raising when a feature area has no confident
tag_map match, and `pipeline.py` automatically runs `kb_search.py`
against the real Document360 KB in that case. There used to be a
`--discover {tag_map,kb}` flag to choose between the two explicitly; it's
gone, because the choice shouldn't be the caller's to make — a feature
area is either already cached (free) or it isn't (falls back to a live
search), and requiring tag_map seeding first is exactly what hard-blocked
a manual-entry run with `LookupError` on 2026-10-29.

`kb_search.py` walks a real Document360 workspace's category tree
(read-only) and runs a single semantic triage pass over it (one model
call) — the model sees the full change note (including the author's
explicit `affected_content_types`/`unaffected_content_types` lists, when
present) and every article's title and category together, and judges
which are plausibly about the same feature.

**Semantic-only, not hybrid (2026-10-29)**: this used to also run a
deterministic "keyword floor" — a substring match against terms pulled
from the change note's `old`/`new` text — and include its hits
unconditionally alongside the semantic results. Removed because it had
no context awareness: any article whose title or category happened to
contain a matched word was listed as a candidate regardless of whether
it was actually about the same feature, which showed up in practice as
real, visible noise (not just the documented generic-word edge case
below). The trade-off: there's no longer a zero-cost, can't-fail
recall floor underneath triage — discovery now depends entirely on that
one model call being thorough.

Run it standalone:

```
python3 doc_sync/kb_search.py doc_sync/data/changes/my_change.json --product-line "DAP for Web"
```

Or just run the pipeline normally — `pipeline.py run --change-note ... [--product-line NAME] [--only ids] [--limit N]`
falls back to it automatically whenever tag_map has nothing for that
feature area. Either way it only reads for discovery — no queue entries,
no tag_map changes. If a flagged article goes on to get a draft written
and `--live` wasn't passed, the real article's current content is
mirrored into the local mock archive first (`mock_d360.seed_from_real`),
so the actual write still never touches the real API.

**Corrected workspace targeting (2026-10-29)** — this was a real bug, not
a tuning issue: Document360 splits content into entirely separate
project versions (workspaces) per product line — DAP for Web, DAP for
Desktop, Archived, etc. — each with its own independent category tree,
not folders inside one shared KB. `fetch_kb_articles()` originally
defaulted to `client.project_id`, which `.env` points at **Archived**
(correct for `draft_writer.py`'s write-safety sandbox, wrong for
discovery reads). An early version of this file then filtered to a
category folder *named* "DAP for Web" *inside* Archived — a subfolder of
retired articles that happens to share a name with the real product
line — never querying the real, live DAP for Web workspace (1,388
articles) at all. `product_line` now resolves to the actual workspace
via `list_project_versions()` (see `_resolve_project_version_id()`)
instead of filtering a category name within whatever workspace was
already configured. **Every candidate count and test record from before
this fix was computed against the wrong, archived dataset and should be
disregarded.**

**Not yet done**: validating recall against a known set of real articles
in the correct workspace (everything tested so far was against the wrong
one). The opt-in-vs-default question is resolved (2026-10-29):
`kb_search.py` is now the automatic fallback whenever `tag_map.py` has no
entry for a feature area, not a separately chosen mode — see "Live KB
search" above.

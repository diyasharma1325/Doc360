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
- **Six live workspaces are in scope, for reads and writes alike**
  (`core/workspaces.py`): DAP for Web, DAP for Desktop, DAP on OS, DAP for
  Mobile, Product Analytics and Whatfix Mirror. Anything else — Archived,
  Seek, and the non-public workspaces — is refused. Seek is excluded for
  now by decision (2026-11-04), not by limitation.
- **Title-only discovery is still the default.** Index discovery
  (`--discovery index`, all six workspaces) is opt-in until it has been
  compared against title-only discovery on real change notes — see
  "Index discovery" below.

## Files

| File | Stage | Role |
|---|---|---|
| `change_note.py` | 1 | Defines and validates the change-note shape |
| `tag_map.py` | 2 (state) | Optional feature-area -> article-id cache, hand-seeded; never required |
| `candidates.py` | 2 | Looks up candidates from the tag map (fuzzy-match fallback on `feature_area` typos); returns `[]`, not an error, when there's no confident match, so `pipeline.py` can fall back to a live search |
| `kb_search.py` | 2 | Live search, two modes. **titles** (default): walks one real Document360 workspace and semantically triages every title against the change note (one model call). **index** (opt-in): searches article bodies across all six live workspaces with `kb_index.py`, then triages only that shortlist. `pipeline.py` runs this automatically whenever `candidates.py` finds no tag_map entry — see "Live KB search" and "Index discovery" below |
| `kb_index.py` | 2 (state) | Local full-text index of every published article body in the six live workspaces (`data/knowledge.db`, git-ignored). `build` (~30-40 min, read-only), `status`, `search`. Built all-or-nothing |
| `kb_search_prompt.md` | 2 (experimental) | Fixed task instructions for `kb_search.py`'s triage call |
| `assess.py` | 3 | Claude path — needs `ANTHROPIC_API_KEY`, not currently default |
| `assess_gemini.py` | 3 | **Gemini path — current default**, needs `GEMINI_API_KEY` |
| `assess_prompt.md` | 3 | Fixed task instructions, concatenated at runtime with `guidelines/document360-formatting.md`, `guidelines/whatfix-writing-guidelines-agent.md` and the article's product reference files; shared by both assess modules |
| `product_context.py` | 2-3 | Picks which product reference files a prompt carries, by product line — the article's own workspace first, then the change note's `product_line`, then DAP for Web |
| `dap-core.md`, `dap-web.md`, `dap-desktop.md`, `dap-os.md`, `dap-mobile.md`, `product-analytics.md`, `mirror.md` | 2-3 (reference) | Product reference files: concepts, terminology, and a fixed snapshot of each workspace's category structure. The four `dap-*` surface files are deltas on `dap-core.md` and always load with it |
| `draft_writer.py` | 4 | Only file that writes to Document360. Checks for an existing draft FIRST, then forks the article into a new draft version and writes into that; never publishes |
| `verify.py` | 4 | Cheap post-write checks (old text gone, new text present, HTML intact, no images lost), shown to the reviewer before they decide |
| `review_queue.py` | 5 | JSON-backed pending/approved/rejected/merge_conflict queue |
| `gemini_call.py` | 2-3 | Every Gemini call goes through here: retries, a per-call token report, and the opt-in local response cache (`DOC_SYNC_LLM_CACHE=1`) |
| `mock_d360.py` | — | Local file-backed stand-in for Document360, including the fork; current default target |
| `pipeline.py` | orchestrator | `run` and `review` CLI commands |
| `../core/workspaces.py` | — | The six live workspaces Doc Sync may read from or write to. Fails closed |
| `../core/d360_client.py`, `../core/articles.py` | — | Document360 API client; `ArticleService.fork_and_update()` is the live draft write |

## Setup

```
pip install -r requirements.txt
```

Requires everything already in `.env` (`D360_API_KEY`, `D360_PROJECT_ID`,
`D360_FOLDER_ID`, `D360_USER_ID`) plus `GEMINI_API_KEY` (currently
required — it's the default provider). `ANTHROPIC_API_KEY` is only
needed if you explicitly pass `--provider claude`. `beautifulsoup4` (in
`requirements.txt`) is needed only to build the knowledge index.

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
2. **Optional: build the knowledge index**, needed only for
   `--discovery index`:
   ```
   python3 doc_sync/kb_index.py build
   ```
   Read-only, ~30-40 minutes, and keep the machine awake and online — a
   network drop longer than about a minute aborts the build and leaves any
   existing index untouched. Re-run it whenever you want fresher results;
   `python3 doc_sync/kb_index.py status` shows its age, and discovery
   warns once it's over 48 hours old.

## Running it

```
python3 doc_sync/pipeline.py run --change-note doc_sync/data/changes/my_change.json
python3 doc_sync/pipeline.py review list
python3 doc_sync/pipeline.py review approve <item_id>
python3 doc_sync/pipeline.py review reject <item_id>
```

The `run` command above defaults to `--provider gemini` against the mock
archive — add `--live` once real Document360 access is available, and
`--provider claude` once `ANTHROPIC_API_KEY` is confirmed. Add
`--discovery index` to search all six live workspaces with the knowledge
index instead of walking one workspace's titles (`--product-line` then
narrows it to one workspace).

`review approve`/`reject` only updates the queue's own record — it does
not call Document360 again. Publishing a written draft, and discarding a
rejected one, both stay manual actions you take directly in Document360.

## Saving tokens while testing

Every Gemini call prints what it spent (`in / out, of it thinking`).
To replay instead of re-spending, set `DOC_SYNC_LLM_CACHE=1`:

```
DOC_SYNC_LLM_CACHE=1 python3 doc_sync/pipeline.py run --change-note ...
DOC_SYNC_LLM_CACHE=1 python3 doc_sync/webapp.py
```

A request that is exactly the same as one already sent (same change
note, same article content, same prompt and reference files, same
model settings) is answered from `data/llm_cache/` at 0 tokens; any
difference makes a real call. It is off by default, so leave it unset
for a live demo. Delete `data/llm_cache/` to start fresh.

Gemini's own context caching is not used: this key is on the free tier,
whose cached-content storage limit is 0 (refused on 2026-11-06).

## Document360 API behavior — verified 2026-11-04

The three assumptions this section used to list as open were checked
with read-only calls against live DAP for Web articles (published,
published-with-a-pending-draft, and never-published), and all held:

- **The read path works.** `GET /Articles/{id}?langCode=en` (now used)
  and `GET /Articles/{id}/{lang}` return identical data.
- **`status` is reliable on the single-article read.** `0` matched "the
  latest version is an unpublished draft" every time, `3` matched
  published. It does NOT hold on the category tree: the tree's
  per-article `status` disagreed with the article read on ~200 DAP for
  Web articles, so nothing in Doc Sync reads draft state off the tree.
- **`version_number` is present**, and is the LATEST version, draft or
  not. The read also carries `public_version`, `latest_version`,
  `category_id` and `project_version_id` (the article's workspace).

Two more behaviors are now handled in code: Document360 can answer
HTTP 200 with `success: false` in the body, so the article read and the
fork/update calls check that flag; and an update into a forked draft
must send `content` (not `html_content`), leave out `content_type`, and
send `translation_option` as the string `"0"`.

**Still unverified: the live fork-and-update write itself.** It has been
tested only against the mock and a recording fake client, since a real
test creates a draft on a live article. Do the first `--live` run on one
low-traffic article, then discard the draft in Document360.

## Live draft writes (fork, then write)

`draft_writer.py` never edits a live article in place. For a flagged
article, in this order:

1. **Draft check, before anything is written.** The article is flagged
   `merge_conflict` (nothing forked, nothing written) if EITHER
   `status == 0` OR `latest_version > public_version`. The two signals
   agreed on every live article checked; the second exists so one stale
   or missing field can't make in-progress work look safe to fork over.
2. **Workspace check**, off the live article's own `project_version_id`
   (not the index, which can be a day old): it must be one of the six
   live workspaces, so a live draft write can never land in Archived.
3. **Fork**: `PUT /Articles/{id}/fork` creates a new draft version; the
   published version is untouched until someone publishes the draft by
   hand in Document360.
4. **Write** the corrected HTML into that new draft version, then
   `verify.py` re-reads it.

A fork is itself an unpublished draft, so re-running the same change
note finds it at step 1 and flags a merge instead of forking twice.
Forks are created as `D360_USER_ID`, so drafts are attributed to that
account — kept for now (2026-11-04), to revisit before real live writes.
The mock models the same fork, so mock runs exercise the same path.

## Live KB search (automatic fallback, no flag to pick it)

Whether a live search runs is still automatic (tag_map hit or not, as
below). HOW it searches is the separate `--discovery` choice — titles
(default) or index — covered in "Index discovery" after this section.

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
disregarded.** Since 2026-11-04 names resolve against
`core/workspaces.py`'s allow-list instead, which refuses Archived and
every other non-live workspace by name and by id — the structural fix
for this class of bug, not just this instance of it. `prd_intake.py`
likewise only offers the six live names to the model.

## Index discovery (`--discovery index`, opt-in)

Title-only discovery has two limits that better triage can't fix: it can
only find an article whose TITLE names the feature, and it sees one
workspace at a time — widening it to six would make the largest prompt
in the pipeline six times larger. Index discovery addresses both:

1. `kb_index.py` holds the full text of every published article in the
   six live workspaces, searched locally at no model cost (SQLite FTS5,
   BM25 ranking, titles weighted above bodies).
2. The search text is the change note's feature area, summary, OLD
   wording (per content type when it has `changes`) and affected content
   types. Deliberately excluded: the `new` wording (a stale article
   doesn't contain it yet), `notes` and `unaffected_content_types` —
   exclusion language like "Pop-ups did NOT move" is what once mined
   wrong keywords into discovery.
   An article must also mention the feature itself — one of the
   affected content types, a change's content type, or the feature area
   (slug dashes read as spaces) — and that match counts twice as much as
   the rest of the wording. Without this, everyday words ("display",
   "text", "dashboard", each in a third of all articles) decided the
   ranking and pop-up or Mirror articles that never mention the feature
   filled the shortlist (2026-11-06). If no article mentions the feature
   names at all, the search falls back to the whole note's wording.
   "Popups"/"Popup" also match the hyphenated "Pop-ups" most articles
   use.
3. Each workspace is searched separately and capped at 12, so DAP for
   Web (about half of all articles) can't crowd the others out; the
   merged list is cut to the best 40.
   Exception: when the feature's own name is rare (30 articles or
   fewer, e.g. "display name" in 28), every article naming it goes on
   the shortlist first, whatever its workspace, and the rest is filled
   as above. The per-workspace cap otherwise cut 20 of the 26 DAP for
   Web articles naming "display name" (2026-11-06). A common name
   ("smart tips", 315) or one matching nothing leaves the search as is.
4. That shortlist, each entry with its workspace and the matching
   excerpt, goes to the same triage call, told it's a keyword-matched
   shortlist rather than a full list. An id the model returns that
   wasn't on the shortlist is dropped.

**This is not the removed keyword floor coming back.** The floor
included keyword hits unconditionally; here every hit is still only a
candidate the model has to accept, with the excerpt to judge it by.

Two trade-offs, both open to revisit after comparison runs:
- **No product reference files in index-mode triage.** Its shortlist
  spans up to six products whose files total ~175 KB, which would put
  back the prompt size the shortlist exists to cut; the excerpts carry
  the concrete text instead. Assessment still loads each article's own
  product files.
- **The index holds each article's LATEST version** — for an article
  with a pending draft, the draft's text. Harmless for discovery, since
  such an article is flagged for a manual merge anyway.

The index is built all-or-nothing: a build writes a fresh database and
swaps it in only once every article read has succeeded, so a failed
build leaves the previous index exactly as it was. There is no
per-workspace build, since one would replace a six-workspace index with
a one-workspace one. Nothing rebuilds it automatically.

## Product reference per workspace

Assessment and title-only triage load the product reference files for
the right product line (`product_context.py`): the article's own
workspace (read off the live article), else the change note's
`product_line`, else DAP for Web. A prompt that names no product line is
built exactly as before this existed. The content maps inside these
files are fixed snapshots; the knowledge index is the up-to-date source.

## Not yet done

- **Compare index discovery against title-only discovery** on the same
  real change notes before making index the default. Until then index
  mode is opt-in, and `webapp.py`'s Discover screen still uses titles.
- **Validate recall** against a known set of real articles in the
  correct workspaces (everything tested before 2026-10-29 was against the
  wrong one).
- **The first live fork-and-update write** (see "Document360 API
  behavior" above).
- **Decide the fork author** (`D360_USER_ID` for now).

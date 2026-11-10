# Doc Sync Pipeline

Finds the live Document360 articles a shipped change has made inaccurate,
and drafts the corrections. A run starts from a **simulated Jira ticket**
and moves across the I2P board's statuses: intake (the ticket becomes a
structured change note), phase 1 (a numbered candidate plan the writer
revises and approves by number), phase 2 (each approved article assessed,
its correction drafted and verified), and a Jira-style artifact showing
the whole run. The `doc-sync` Claude Code skill drives it end to end; see
"Ticket runs" below. Nothing is ever published, and live articles are only
read.

`pipeline.py run` is the older entry point, for a hand-written change-note
file; it still works, against the local mock archive by default. Tag-map
learning (recording confirmed candidates back into `tag_map.json`) is not
built.

**Standing decisions, current as of this doc:**
- **Claude is the default provider** (since 2026-11-06) for triage and
  assessment, called through `claude -p` on the writer's Claude Code
  login (`claude_call.py`, `claude-sonnet-5-5`), so no
  `ANTHROPIC_API_KEY` is needed. **Gemini is the fallback**
  (`--provider gemini`, `gemini-3.5-flash`, needs `GEMINI_API_KEY`).
- **Live articles are only read.** Ticket runs save drafts in the run
  folder, or write them into Archived scratch articles the writer lists
  (`archived_writer.py`, built but not used live yet). `pipeline.py run`
  writes to the local mock archive (`mock_d360.py`) unless `--live`.
- **Six live workspaces are in scope** for discovery and assessment
  (`core/workspaces.py`): DAP for Web, DAP for Desktop, DAP on OS, DAP for
  Mobile, Product Analytics and Whatfix Mirror. Anything else — Archived,
  Seek, and the non-public workspaces — is refused. Seek is excluded for
  now by decision (2026-11-04), not by limitation.
- **Ticket runs use agent discovery by default** (`agent`, 2026-11-10):
  Claude agents with read-only tools search and read a plain-text copy of
  each workspace the ticket names. `index` (keyword search of article
  bodies plus triage) was the default before; `both` adds a strict title
  check to it. `pipeline.py run` and `kb_search.py` still default to
  title-only discovery. See "Discovery scope", "Agent discovery" and
  "Index discovery" below.

## Files

| File | Stage | Role |
|---|---|---|
| `ticket.py` | 1 | The simulated Jira ticket a run starts from (summary, free-text description, PDF attachments, assignee) in its own `runs/<name>/` folder, and the local recorder for its status moves and comments (`out/jira_log.json`, `out/comment-NN.txt`). Nothing touches a real Jira |
| `ticket_intake.py` | 1 | The ticket -> a change note, in one model call (`ticket_intake_prompt.md`). Extracts the product lines the writer named and bounces the ticket to To Do if none is named |
| `ticket_run.py` | 1-4 | The ticket's steps: `intake`, `phase1` (discovery -> numbered candidate plan comment, In Draft -> Peer review), `replan` (writer feedback -> revised plan), `approve` (plan numbers -> `approved.json`, Peer review -> For review), `phase2` (assess approved articles, save or write drafts, final comment), `show` |
| `build_artifact.py`, `artifact_template.html` | 5 | The Jira-style artifact page for a run, as the I2P backtest builds one: ticket header, details sidebar, activity timeline (status moves, comments reproduced exactly, the extracted change note, the approval), proposed edits as word-level before/after diffs, and a footnote on how the run differs from production. Writes `runs/<name>/artifact.html`; publish it with the Artifact tool |
| `archived_writer.py` | 4 | The only way a ticket run writes to Document360: into the writer's listed Archived scratch articles, never a live one. Refuses unlisted ids and anything not in the Archived workspace, names every target before an overwrite, direct update (never a fork or publish) |
| `pdf_text.py` | 1 | Ticket PDF attachments -> text (pdfplumber, tables as Markdown), with the I2P agent's 10 MB / 300-page limits |
| `change_note.py` | 1 | Defines and validates the change-note shape, including the `product_lines` list |
| `tag_map.py` | 2 (state) | Optional feature-area -> article-id cache, hand-seeded; never required |
| `candidates.py` | 2 | Looks up candidates from the tag map (fuzzy-match fallback on `feature_area` typos); returns `[]`, not an error, when there's no confident match, so `pipeline.py` can fall back to a live search |
| `kb_search.py` | 2 | Live search, scoped to the change note's product lines (see "Discovery scope" below), two modes. **titles** (default): walks each workspace in scope and semantically triages every title against the change note (one model call per workspace). **index** (opt-in): searches article bodies in scope with `kb_index.py`, then triages only that shortlist. `pipeline.py` runs this automatically whenever `candidates.py` finds no tag_map entry — see "Live KB search" and "Index discovery" below |
| `kb_index.py` | 2 (state) | Local full-text index of every published article body in the six live workspaces (`data/knowledge.db`, git-ignored). `build` (~30-40 min, read-only), `status`, `search`. Built all-or-nothing |
| `old_terms_prompt.md` | 1 | Instructions for intake's second call, which suggests the old wording when the ticket gives none (see "Old wording") |
| `kb_mirror.py` | 2 | Exports the knowledge index to a plain-text copy, one `.md` per article (`data/kb_mirror/`, git-ignored, seconds, no network), for agent discovery |
| `discovery_agent.py`, `discovery_agent_prompt.md` | 2 | Agent discovery: read-only Claude agents over the copy, two runs per workspace within a per-ticket budget, verdicts with an edit/archive action, keyword-triage fallback (see "Agent discovery") |
| `eval_recall.py`, `eval/keys/` | — | Discovery recall benchmark: scores the shortlist (free) and the plan (`--triage`) against writer-confirmed answer keys (see "Recall benchmark") |
| `kb_search_prompt.md` | 2 (experimental) | Fixed task instructions for `kb_search.py`'s triage call |
| `assess.py` | 3 | **Claude path — default**, through `claude_call.py`; no API key needed |
| `assess_gemini.py` | 3 | Gemini path — fallback (`--provider gemini`), needs `GEMINI_API_KEY` |
| `assess_prompt.md` | 3 | Fixed task instructions, concatenated at runtime with `guidelines/document360-formatting.md`, `guidelines/whatfix-writing-guidelines-agent.md` and the article's product reference files; shared by both assess modules |
| `product_context.py` | 2-3 | Picks which product reference files a prompt carries, by product line — the article's own workspace first, then the change note's `product_line`, then DAP for Web |
| `dap-core.md`, `dap-web.md`, `dap-desktop.md`, `dap-os.md`, `dap-mobile.md`, `product-analytics.md`, `mirror.md` | 2-3 (reference) | Product reference files: concepts, terminology, and a fixed snapshot of each workspace's category structure. The four `dap-*` surface files are deltas on `dap-core.md` and always load with it |
| `draft_writer.py` | 4 | Only file that writes to Document360. Checks for an existing draft FIRST, then forks the article into a new draft version and writes into that; never publishes |
| `verify.py` | 4 | Cheap post-write checks, shown to the reviewer before they decide: old wording that was in the article word for word is gone, HTML intact, no big shrink, no images lost. (No "new text present" check since 2026-11-06: a change note's `new` is a summary sentence, so it fired on nearly every draft) |
| `review_queue.py` | 5 | JSON-backed pending/approved/rejected/merge_conflict queue |
| `claude_call.py` | 2-3 | Every Claude call goes through here: `claude -p` with `--json-schema` structured output, run from a temp folder outside the repo (so no `CLAUDE.md` is loaded) with `ANTHROPIC_API_KEY` stripped; retries, a per-call report, a call log (`data/model_calls.jsonl`) and the shared local response cache. `python3 doc_sync/claude_call.py selftest` checks it works |
| `gemini_call.py` | 2-3 | Every Gemini call goes through here: retries, a per-call token report, and the opt-in local response cache (`DOC_SYNC_LLM_CACHE=1`) |
| `mock_d360.py` | — | Local file-backed stand-in for Document360, including the fork; current default target |
| `pipeline.py` | orchestrator | `run` and `review` CLI commands |
| `../core/workspaces.py` | — | The six live workspaces Doc Sync may read from or write to. Fails closed |
| `../core/d360_client.py`, `../core/articles.py` | — | Document360 API client; `ArticleService.fork_and_update()` is the live draft write |

## Setup

```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

**Run every command with `.venv/bin/python`**, not the system `python3`:
the macOS system Python has none of these packages, so it fails on the
first import. The commands below write `python3` for brevity.

Requires everything already in `.env` (`D360_API_KEY`, `D360_PROJECT_ID`,
`D360_FOLDER_ID`, `D360_USER_ID`), plus the `claude` CLI installed and
logged in (`python3 doc_sync/claude_call.py selftest` should answer) for
the default provider. `GEMINI_API_KEY` is needed only for
`--provider gemini` (including `ticket_run.py intake --provider gemini`).
`ANTHROPIC_API_KEY` is never
needed, and is stripped from `claude -p`'s environment if set, so calls
always run on the Claude Code login. `beautifulsoup4` (in
`requirements.txt`) is needed only to build the knowledge index.

All commands below assume you're running from the repo root (`Doc360/`),
same as `core/cli.py` and `core/discover.py` — `doc_sync/assess.py` and
`doc_sync/draft_writer.py` add `core/` to `sys.path` themselves, so
this works regardless of where you invoke it from.

## Ticket runs (the Jira-style entry point)

A run starts from a **simulated Jira ticket**, as in the I2P backtest:
there is no real Jira and nothing is ever posted to one. The writer gives
the ticket's summary, a free-text description and any PDF attachments
(PRDs, product notes):

```
python3 doc_sync/ticket.py new dap-display-names --assignee "Your Name" \
    --summary "Display Name for Whatfix content" \
    --description-file desc.txt --attach "Product Note.pdf"
python3 doc_sync/ticket_run.py intake  dap-display-names              # To Do -> In Draft
python3 doc_sync/ticket_run.py phase1  dap-display-names [--discovery both]    # In Draft -> Peer review + plan
python3 doc_sync/ticket_run.py replan  dap-display-names "Drop 2; also check Task List articles"
python3 doc_sync/ticket_run.py approve dap-display-names "1, 3-5"       # Peer review -> For review
python3 doc_sync/ticket_run.py phase2  dap-display-names               # drafts saved in the run folder
python3 doc_sync/ticket_run.py phase2  dap-display-names \
    --archived-targets "<archived link 1>, <archived link 2>, ..." --confirm-overwrite   # (not used yet)
python3 doc_sync/ticket_run.py show    dap-display-names               # status, plan, approval
python3 doc_sync/ticket.py show dap-display-names                      # ticket + every recorded event
```

Each run gets its own folder, `doc_sync/runs/<name>/` (git-ignored): the
ticket, copies of its attachments, the extracted `change_note.json`, and
`out/`, where every status move and comment the pipeline would make on a
real ticket is recorded (`jira_log.json`, `comment-NN.txt`). The statuses
are the I2P board's: To Do -> In Draft -> Peer review -> For review.

**Product lines are a prerequisite.** Name them anywhere in the summary or
description, in your own words ("ships on web and desktop"). Intake maps
them onto the six live workspaces and records the exact words it took
them from. It never picks one itself, and never takes one from an
attachment alone. A ticket that names none is **bounced**: a comment says
what to add, the ticket moves back to To Do, and no change note is saved.
Fix it with `ticket.py update <name> --description-file ...` and run intake
again. An attachment that can't be read (over 10 MB or 300 pages, not a
PDF, or a scanned image with no text) doesn't stop the run; a comment
says it wasn't used. A failed model call also moves the ticket back to To
Do with a comment, so it can always be retried.

**Old wording** (2026-11-09). Outdated articles describe the old state in
the old words ("Widgets page"), so intake extracts them as `old_terms`
when the ticket or an attachment says what the old state was called.
When it doesn't, a second small call suggests some from the product
reference for the ticket's product lines (`old_terms_suggested`, Claude
only), and an "old wording" comment lists them for the writer to confirm.
Discovery searches for both. The writer corrects them on a re-plan:
`ticket_run.py replan <name> --old-terms "Widgets page, Widgets section"`
replaces intake's terms in the saved change note. A suggestion is only as
good as the product reference: the Unified Content Experience section in
`dap-core.md` is what lets it name "Widgets page" for the Launchers change.

**Phase 1: the candidate plan** (`ticket_run.py`). Discovery runs on the
change note within the ticket's product lines (see "Discovery scope"
below), in **agent** mode by default on ticket runs (decided 2026-11-10,
see "Agent discovery"; `--discovery index` is the keyword search,
`--discovery both` adds a strict title check to it, `--discovery titles`
is title-only), and the result is recorded as a numbered **candidate plan**
comment, moving the ticket In Draft -> Peer review. The plan is saved as
`plan.json`. `tag_map.json` is not used on ticket runs: its ids are mock
fixtures, not live articles. A failed phase 1 records a "plan failed"
comment and leaves the ticket in In Draft to run again.

**Revising the plan.** `replan` records the writer's feedback as their
comment and re-runs triage with that feedback plus the numbered plan they
saw, so "drop 2 and 6" or "also include Task List articles" work. In index
mode the feedback's own wording is also searched locally and up to 12
matches join the shortlist, since triage can only pick from what it's
shown. `--product-lines` changes the scope. The ticket stays in Peer
review; each revision is a new comment and a new `plan.json` version.

**Approval is by plan number, never by typed article id** (`1, 3, 5-7` or
`all`): each number is checked against the plan, the chosen articles are
saved as `approved.json`, and the ticket moves Peer review -> For review.
After that, re-planning and re-approving are refused. A typed id once sent
a test run after an article that doesn't exist (2026-11-06); numbers can't.

**Phase 2: assessing and drafting** (`ticket_run.py phase2`, For review).
Each approved article, in plan order, is read live and assessed against
the change. For one that needs an edit, its before and after HTML are
saved in `out/articles/` (`NN-<slug>.before.html` / `.after.html`), then:

- **Live article already has an unpublished draft** -> "Needs a manual
  merge". Nothing is written; the proposed edit stays in the run folder.
  The same check a live write will need, applied now even though no live
  article is ever written.
- **No Archived targets given** -> "Draft saved locally", verified against
  the saved HTML.
- **Archived targets given** -> written into the next unused one
  (`archived_writer.py`), then read back and verified. **Live articles are
  never written**: only Archived scratch articles the writer listed, one
  per approved article (checked before any model call). Every target is
  read first and refused unless it is in the Archived workspace; without
  `--confirm-overwrite` the run names each target's current title and
  stops, since an overwrite has no undo.

Results are saved after every article (`results.json`), so re-running
phase 2 retries only the failed ones and puts them in the next unused
target. The final "drafts ready" comment lists every article's outcome,
confidence and reason; the ticket stays in For review, as on the I2P board.
Ticket runs don't use `review_queue.json`: the ticket is the review surface.

**Archived writes are built but not used yet** (decision 2026-11-07): the
write path and its guard are tested against a fake client only. Live
Archived writes start once the whole pipeline is finished and tested end
to end with the Jira-style artifact.

**The Jira-style artifact.** At any stage, a run can be shown as a Jira
issue page, as the I2P backtest shows its runs:

```
python3 doc_sync/build_artifact.py dap-display-names --title "Display Names Doc Sync"
```

writes `runs/<name>/artifact.html`, which is then published (privately)
with Claude's Artifact tool. It shows the ticket, every recorded status
move and comment in order (reproduced exactly; the Markdown comments are
rendered by a small built-in renderer, no extra package), the extracted
change note with the words the product lines came from, the approval,
and every proposed edit as a word-level diff of the article's visible
text. Whatever hasn't happened yet is simply left out, so the page can be
rebuilt and republished to the same link as the run goes on.

**The `doc-sync` skill** (`.claude/skills/doc-sync/SKILL.md`) drives a whole
run from Claude Code, the way the I2P backtest skill does: it asks the writer
for the ticket (never guessing a missing input), runs each step above, shows
the plan exactly as recorded and asks for approval by number or a revision,
asks before any Archived write after naming every target, runs phase 2, and
builds and publishes the artifact. In Claude Code, ask to "run doc sync on a
ticket" or type `/doc-sync`. The skill only runs commands; it never edits the
pipeline code.

The local web app (`webapp.py`) and its PRD intake (`prd_intake.py`) were
removed on 2026-11-07: the ticket run, the skill and the artifact replace
them.

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

The `run` command above defaults to `--provider claude` against the mock
archive — add `--live` once real Document360 access is available, and
`--provider gemini` to use the Gemini fallback for triage and assessment. Add
`--discovery index` to search article bodies with the knowledge index
instead of triaging every title. Either way the search covers the change
note's product lines; `--product-lines "DAP for Web, DAP for Desktop"`
overrides them for one run.

### Discovery scope

The workspaces searched are the same rule in both modes
(`kb_search.resolve_scope()`), since 2026-11-06:

1. `--product-lines` on the command line, if given (comma-separated);
2. else the change note's own `product_lines`: on a ticket run, the ones
   the writer named, which intake requires;
3. else the mode's old default: DAP for Web for titles, all six for index.

Every name is checked against the six live workspaces, so a scope can never
include Archived or another non-live workspace. Every candidate record
carries the workspace it came from.

**Titles mode makes one triage call per workspace**, each with that
workspace's own product reference files, rather than one call over a
merged listing: DAP for Web alone is ~1,400 titles (~120k prompt tokens),
and a merged listing would go past what has been tested. Measured on
2026-11-06 for a Web + Desktop ticket: 1,933 titles, two calls, ~$0.82,
101 candidates. Index mode on the same ticket: 24 shortlisted, one call,
~$0.13, 12 candidates. Titles sees only titles, so for a broad feature it
over-includes by design; the candidate approval step is where that list
gets cut. That comparison is why ticket runs defaulted to index mode
from 2026-11-07 until agent mode replaced it (2026-11-10; `pipeline.py
run` and `kb_search.py` still default to titles).

**`--discovery both`** (2026-11-07) runs the two together: the index pass
as usual, plus an independent title pass per workspace, run as a strict
recall check on Haiku (`claude-haiku-5-5`) to catch articles whose title
describes the feature in other words but whose text didn't match. The
title pass is not told what the index found, so the two are independent,
and each candidate gets a `found_by`: **both** (listed first: two methods
agree), **index**, or **titles** (listed last; a quick look decides). The
plan comment shows it as a "Found by" column. Measured 2026-11-07:

| Ticket | both / index only / titles only | Cost |
|---|---|---|
| Display Names, Web + Desktop (broad change) | 8 / 4 / 67 | ~$0.17 |
| Smart Tips domain validation, Web + Mobile (narrow) | 1 / 2 / 1 | ~$0.23 |

The title check stays strict on a narrow change and finds genuine gaps on a
broad one (e.g. "Create an Article", "Flow Automation" for Display Names,
both surfaces the product note names). With no knowledge index built,
`both` runs as titles only.

`review approve`/`reject` only updates the queue's own record — it does
not call Document360 again. Publishing a written draft, and discarding a
rejected one, both stay manual actions you take directly in Document360.

## Saving tokens while testing

Every model call prints what it spent: Claude calls as
`model, in / out, seconds, $cost` (and every one is appended to
`data/model_calls.jsonl`), Gemini calls as `in / out, of it thinking`.
The dollar figure is what `claude -p` reports for the call; it counts
against the Claude Code plan, not an API bill. Claude Code caches the
long shared system prompt (style guides plus product files), so
consecutive assessments cost far less than the first (measured
2026-11-06: $0.19 for the first, $0.01–0.03 after).

To replay instead of re-spending, set `DOC_SYNC_LLM_CACHE=1` (works for
both providers):

```
DOC_SYNC_LLM_CACHE=1 python3 doc_sync/pipeline.py run --change-note ...
DOC_SYNC_LLM_CACHE=1 python3 doc_sync/ticket_run.py phase1 <name>
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
python3 doc_sync/kb_search.py doc_sync/runs/<name>/change_note.json [--discovery index] [--product-lines "DAP for Web"]
```

Or just run the pipeline normally — `pipeline.py run --change-note ... [--product-lines NAMES] [--only ids] [--limit N]`
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
for this class of bug, not just this instance of it. Ticket intake
(`ticket_intake.py`) likewise only offers the six live names to the model,
and checks its answer against the same list.

## Index discovery (`--discovery index`, opt-in)

Title-only discovery has two limits that better triage can't fix: it can
only find an article whose TITLE names the feature, and it sees one
workspace at a time — widening it to six would make the largest prompt
in the pipeline six times larger. Index discovery addresses both:

1. `kb_index.py` holds the full text of every published article in the
   six live workspaces, searched locally at no model cost (SQLite FTS5,
   BM25 ranking, titles weighted above bodies).
2. The search text is the change note's feature area, summary, OLD
   wording (per content type when it has `changes`), old terms (stated or
   suggested, see "Old wording" above) and affected content types. Deliberately excluded: the `new` wording (a stale article
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
3. Only the workspaces in scope are searched (see "Discovery scope").
   With several in scope, each is searched separately and capped at 12,
   so DAP for Web (about half of all articles) can't crowd the others
   out; the merged list is cut to the best 40. With one in scope there is
   nothing to balance, so it gets all 40 (2026-11-09: the cap of 12 left
   out most of the 103 DAP for Web articles mentioning Launchers).
   Exception: when the feature's own name is rare (30 articles or
   fewer, e.g. "display name" in 28), every article naming it goes on
   the shortlist first, whatever its workspace in scope, and the rest is filled
   as above. The per-workspace cap otherwise cut 20 of the 26 DAP for
   Web articles naming "display name" (2026-11-06). A common name
   ("smart tips", 315) or one matching nothing leaves the search as is.
4. **Content-type sweep** (2026-11-09). Every article whose TITLE or
   CATEGORY names an affected content type (`CONTENT_TYPES` in
   `kb_search.py`: Flows, Smart Tips, Beacons, Pop-ups, Launchers,
   Blockers, Surveys, Task List, Self Help, Cues, Static Content) joins
   the shortlist ahead of the ranked 40, whatever it ranks: on the
   Launchers ticket, ranking alone shortlisted 7 of the 27 articles a
   writer expected, because "Dashboard" and "Studio" articles outranked
   "What are Launchers?". A UI surface the ticket names ("Dashboard",
   "Content tab") is not swept: it's in hundreds of articles. The sweep
   holds at most 120, shared equally between the types (Flows alone is
   ~190 in DAP for Web), best match to the change first; the plan
   comment says how many of each type were checked, and lists by title
   every swept article triage left out, so the writer can add one back.
   Swept entries are marked `about: <type>` and triage is told to keep
   them unless they plainly can't be affected.
5. That shortlist, each entry with its workspace and the matching
   excerpt, goes to triage in batches of 40 (one call each), each batch
   told it's a shortlist rather than a full list, told it's a keyword-matched
   shortlist rather than a full list. An id the model returns that
   wasn't on the shortlist is dropped (title mode applies the same check
   to its full listing since 2026-11-06).

**This is not the removed keyword floor coming back.** The floor
included keyword hits unconditionally; here every hit is still only a
candidate the model has to accept, with the excerpt to judge it by.

Two trade-offs, both open to revisit after comparison runs:
- **Product reference files in index-mode triage only within 90 KB.**
  Since 2026-11-06 the triage call loads the reference files for the
  workspaces in scope when they total 90 KB or less (Web + Desktop: 65 KB;
  all four DAP surfaces: 102 KB; all six: 177 KB). Above that it triages on
  the excerpts alone, as before, so a wide scope doesn't put back the
  prompt size the shortlist exists to cut. Assessment still loads each
  article's own product files.
- **The index holds each article's LATEST version** — for an article
  with a pending draft, the draft's text. Harmless for discovery, since
  such an article is flagged for a manual merge anyway.

**What the index reads** (2026-11-09): each article's visible text, plus
the alt text of each image, where the image sits (a bare file name or a
generic "image" is skipped). Screenshots carry much of an article's
context ("Customize a Launcher": 11 images, 335 words, and "Dashboard"
only in its screenshots); alt text is the free part of that. Text INSIDE
screenshots (OCR) and semantic search are planned next. `status` shows
`body_includes`; an index built before this says "text".

**Recall benchmark** (`eval_recall.py`, 2026-11-09). Answer keys in
`eval/keys/` list the articles a change really affects, confirmed by a
writer. The script scores SHORTLIST recall (free, no model call: what
reached the model) and, with `--triage`, PLAN recall (after triage),
lists what was missed at each stage, and lists plan articles not in the
key as "extra" rather than wrong. Run it before and after any change to
discovery. Two keys, both confirmed by a writer (2026-11-10):
`launchers-content-tab` (13 affected) and `ai-popups-deprecation` (7
affected, one to archive; a HYPOTHETICAL change used only for testing).
A key may also list `not_affected` articles (so a plan's wrong picks are
told apart from articles nobody has reviewed), `ignore` (left out of
scoring) and `"action": "archive"` on an expected article (scored against
agent mode's archive flags). `--discovery agent` scores agent mode.

## Agent discovery (`--discovery agent`, the ticket-run default)

Why: index triage judges each shortlisted article from its title and a
~30-word excerpt, with no tools, so it drops articles whose excerpt
doesn't look affected and can never find one the keyword search didn't
shortlist. Agent mode gives Claude read-only Grep / Glob / Read over a
plain-text copy of the workspace (`kb_mirror.py`, made from the index),
so it can open articles and follow leads.

- One agent per workspace in scope, each in a temporary copy of that
  workspace outside the repo. The index shortlist is its must-review
  list: every article on it gets a verdict, and one it doesn't judge is
  kept as "possibly affected".
- Verdicts: affected, potentially affected, not affected, with an
  action: edit, or **archive** (the article's main subject is removed).
  The not-affected verdicts are saved in `plan.json` with reasons.
- Two runs per workspace, merged (the most cautious verdict wins): one
  run varies. A per-ticket budget (`--agent-budget`, or
  `$DOC_SYNC_AGENT_BUDGET`, default $5) decides how: two full runs at
  once when it covers them everywhere, else run 1 everywhere first and
  then a full second run, a cheaper recheck of what run 1 cleared, or
  nothing, by what's left. Each run is capped by the CLI's
  `--max-budget-usd` (checked between turns, so a run can go a little
  over).
- Fallback: a workspace where no run succeeded is triaged the index way
  instead, and the plan comment says so. Gemini (`--provider gemini`)
  runs as index mode.
- Cost: each step prints its model cost and logs a `cost` event in
  `out/jira_log.json`. It is deliberately NOT in the plan, comments or
  the artifact (writer decision, 2026-11-10).

Measured 2026-11-10 (two confirmed keys, DAP for Web): agent 19 of 20
affected articles found, plans of 7 and 19; index 17 of 20, plans of 18
and 34. Agent ~$0.50 and ~1 minute per single-workspace ticket; index
~$0.10 and ~25 seconds. Known gaps: phase 2 doesn't act on "archive" yet;
headings aren't marked in the copy (the index stores flattened text).

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

- **The end-to-end test with Archived writes**: one ticket run through the
  `doc-sync` skill, writing its drafts into Archived scratch articles, then
  the artifact. Archived writes have so far been tested against a fake
  client only (decision 2026-11-07).
- **Compare discovery modes on more tickets.** Index became the ticket-run
  default after one broad and one narrow ticket (2026-11-07); `both` is
  there to check whether the title pass keeps finding real gaps.
- **More answer keys.** The benchmark has one draft key; recall on one
  ticket says little. Each real ticket run whose plan a writer corrects
  is a key waiting to be written down.
- **Text inside screenshots (OCR, tesseract) and semantic search**
  (embeddings beside the keyword search), planned together.
- **Validate recall** against a known set of real articles in the
  correct workspaces (everything tested before 2026-10-29 was against the
  wrong one).
- **The first live fork-and-update write** (see "Document360 API
  behavior" above).
- **Decide the fork author** (`D360_USER_ID` for now).

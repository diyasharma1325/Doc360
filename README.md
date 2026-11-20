# Doc Sync

An MVP automation pipeline that keeps Document360 support articles in sync
with shipped product changes. Given a change note describing something
that just shipped (a feature, a behavior change, a new option), it finds
the Document360 articles that might now be wrong, drafts a fix with an
LLM, and queues it for human review — never publishing or overwriting
anything on its own.

The full pipeline design, decisions, and status live in
[`doc_sync/README.md`](doc_sync/README.md) — this file is just the map of
how the pieces fit together.

## Layout

| Path | What it is |
|---|---|
| [`doc_sync/`](doc_sync/README.md) | The pipeline itself: change notes in, candidate discovery (title triage, or a local full-text index across all six live workspaces), LLM assessment, fork-then-write draft writes with safety checks, review queue. Start here. |
| `.claude/skills/doc-sync/` | The `doc-sync` Claude Code skill: drives a Doc Sync run from a simulated Jira ticket to drafts and a published Jira-style artifact. Type `/doc-sync` in Claude Code. |
| `.claude/skills/doc-sync-judge/` | The `doc-sync-judge` skill: scores a phase 2 draft against a rubric for the edit (change coverage, accuracy, preservation) and returns a confidence score and badge. |
| `core/` | Shared Document360 API client (`d360_client.py`), the live-workspace allow-list every discovery read and live draft write is checked against (`workspaces.py`), and manual article tools (`articles.py`, `cli.py`, `discover.py`) used both by `doc_sync/` and for one-off manual testing against the real API. |
| `guidelines/` | House writing-style and HTML-formatting references (`document360-formatting.md`, `whatfix-writing-guidelines-agent.md`) that the pipeline's assessment step reads on every run, so drafts come out in-house-style by construction. |
| `inputs/` | Material from outside the pipeline: `drafts/` (hand-authored or manually repaired article HTML), `prds/` (PRDs and product notes, kept local and git-ignored) and `assets/` (reference media such as product-capture videos, kept local and git-ignored). |

## Setup

```
pip install -r requirements.txt
```

See [`doc_sync/README.md`](doc_sync/README.md) for required environment
variables and how to run the pipeline. Testing it for the first time? Start
with [`TESTING.md`](TESTING.md).

## Note

This repo used to also hold `doc360-ia-audit/`, a separate, unrelated
tool (a read-only structural health check for a Document360 workspace —
duplicate titles, stale content, over-fragmented categories). It shared
no code with Doc Sync and has since moved to its own repo.

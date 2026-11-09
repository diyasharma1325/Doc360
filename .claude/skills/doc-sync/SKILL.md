---
name: doc-sync
description: Run the Doc Sync pipeline on a simulated Jira ticket - a shipped product change described in a ticket summary, free-text description and optional PDF attachments (PRDs, product notes) - to find the live Document360 articles it has made inaccurate and draft the corrections. Walks the ticket through To Do -> In Draft (intake) -> Peer review (candidate plan) -> For review (approval, then drafts), records every status move and comment locally, and publishes the Jira-style artifact. Use when a writer asks to run doc sync, check which articles a change affects, update docs for a shipped change, or run the pipeline on a ticket, PRD or product note.
---

# Doc Sync ticket run

A run answers one question: given a change that shipped, which live Document360
articles are now wrong, and what should they say? It runs the real pipeline code
in `doc_sync/` and drives it through a **simulated** Jira ticket, the way the I2P
backtest does: nothing is posted to a real Jira, and every status move and comment
is recorded in the run's folder.

Never edit the pipeline code during a run. Everything below is a command.

## Ground rules

- **Ask, don't guess.** Collect every input in step 1 from the writer. If one is
  missing, ask for it.
- **Live articles are only ever read.** Phase 2 saves drafts in the run folder, or
  writes them into Archived scratch articles the writer lists. Never anything else.
- **Approval is by plan number** (`1, 3, 5-7` or `all`), never by typing article ids.
- **Confirm before any Document360 write.** Archived targets are overwritten with no
  undo, so name each one's current title and get an explicit yes first.
- **Show the writer what the pipeline produced, not your summary of it.** Plans and
  results are shown as recorded.

## Setup (check once)

All commands run from the repo root (`Doc360/`) with **`.venv/bin/python`**. The
system `python3` has none of the packages and fails on the first import. `$P` below
stands for `.venv/bin/python -W ignore`: write it out in full in each command. Don't
put it in a shell variable; zsh passes `$P` as one word and the command fails.

- `.env` has `D360_API_KEY` (reads only, for discovery and assessment).
- The `claude` CLI is logged in: `$P doc_sync/claude_call.py selftest` answers.
- For index discovery (the default on ticket runs), a knowledge index exists:
  `$P doc_sync/kb_index.py status`. If it's over 48 hours old, say so and offer a
  rebuild (`$P doc_sync/kb_index.py build`, read-only, ~40 minutes, run in the
  background). Don't block the run on it.

## Step 1: Collect the ticket

Ask the writer for:

1. **Summary**: the Jira title, word for word.
2. **Description**: word for word. It must **name the product lines** the change
   ships in (any wording: "web and desktop", "DAP for Mobile", "Mirror"). If it
   doesn't, say intake will bounce it and ask them to add them. The six live
   product lines are DAP for Web, DAP for Desktop, DAP on OS, DAP for Mobile,
   Product Analytics and Whatfix Mirror.
3. **Old wording** (recommended): what the product called the thing before the
   change (the old tab, page, menu or button name, e.g. "Widgets page"). Outdated
   articles still use those words, so they're what finds them. Ask for it to go in
   the description. If the writer doesn't know, intake suggests some.
4. **Attachments** (optional): PDF paths, e.g. a PRD or product note.
5. **Assignee**: the writer's name, shown on the artifact.

Pick a run name: a lowercase slug, `<product>-<feature>` (e.g. `dap-display-names`),
not already in `doc_sync/runs/`. Write the description to a file in your scratchpad
so quotes and line breaks survive, then:

```bash
$P doc_sync/ticket.py new <name> --assignee "<name>" --summary "<summary>" \
    --description-file <desc file> [--attach "<pdf>" ...]
```

## Step 2: Intake (To Do -> In Draft)

```bash
$P doc_sync/ticket_run.py intake <name>
```

- **Bounced** (exit 1, "Bounced to To Do"): show the writer the reasons. Fix the ticket
  with `$P doc_sync/ticket.py update <name> --description-file <file>` and run intake
  again.
- **OK**: show the product lines it found and the words they came from. If the
  writer disagrees, stop and fix the description; don't override silently.
- An "attachments not read" comment means a PDF was skipped (too big, scanned, not a
  PDF). Tell the writer.
- Show the "old wording" comment as recorded. When the terms are **suggested**, ask
  the writer to confirm or correct them. A correction goes in on the plan step:
  `$P doc_sync/ticket_run.py replan <name> --old-terms "<term 1>, <term 2>"`.

## Step 3: Phase 1, the candidate plan (In Draft -> Peer review)

```bash
$P doc_sync/ticket_run.py phase1 <name>                    # index search (default)
$P doc_sync/ticket_run.py phase1 <name> --discovery both   # index + a strict title check
```

Use `both` when the writer asks for a thorough search, or the change is broad (many
content types or surfaces). It adds a "Found by" column; `both` is the strongest
signal. Takes a minute or two.

Show the writer the plan: the latest `doc_sync/runs/<name>/out/comment-NN.txt`,
as plain text, every row, numbered exactly as recorded. Then ask them to either
**approve by number** or **say what to change**.

The plan lists, under the table, every article about an affected content type that
triage **left out**, by title. Show that too: it's where the writer spots a miss.

To revise:

```bash
$P doc_sync/ticket_run.py replan <name> "<the writer's feedback, word for word>" [--product-lines "..."] [--old-terms "..."]
```

`--old-terms` replaces the old wording intake stated or suggested; use it when the
writer corrects it. Feedback can be left out when `--old-terms` is the only change.

Show the revised plan the same way, and ask again. Repeat as needed.

## Step 4: Approval (Peer review -> For review)

```bash
$P doc_sync/ticket_run.py approve <name> "<numbers>"
```

Pass exactly the numbers the writer gave. If it refuses (a number outside the plan),
show the message and ask again.

## Step 5: Phase 2, the drafts

**Default: drafts saved in the run folder only.**

```bash
$P doc_sync/ticket_run.py phase2 <name>
```

**Into Archived scratch articles**, only if the writer asks for it and gives one
Archived portal link per approved article
(`https://portal.document360.io/<project>/document/archived/view/<id>`):

```bash
$P doc_sync/ticket_run.py phase2 <name> --archived-targets "<link 1>, <link 2>, ..."
```

Without `--confirm-overwrite` this only checks the targets and lists each one's
current title. Show the writer that list, say the content and title of each will be
overwritten with no undo, and get an explicit yes. Then run the same command with
`--confirm-overwrite`. Live articles can't be written by any path.

Phase 2 makes one model call per approved article and can take several minutes; run
it in the background. When it finishes, show the "drafts ready" comment (the latest
`comment-NN.txt`) as recorded. If any article **failed**, running phase 2 again
retries only those.

## Step 6: The artifact

```bash
$P doc_sync/build_artifact.py <name> --title "<Feature> Doc Sync"
```

Publish `doc_sync/runs/<name>/artifact.html` with the Artifact tool: `icon: "ticket"`
and a one-sentence description naming the ticket key and the change. Give the writer
the link and remind them it is private until they share it.

The page can be built at any stage. After a later step, rebuild and publish the same
file path again so the link stays the same.

## Files

- `doc_sync/runs/<name>/`: the run (git-ignored). `ticket.json`, `attachments/`,
  `change_note.json`, `plan.json`, `approved.json`, `results.json`, `artifact.html`,
  and `out/` with `jira_log.json`, `comment-NN.txt` and `articles/` (before/after HTML).
- `$P doc_sync/ticket_run.py show <name>`: status, plan, approval and phase 2 results
  at a glance.
- `doc_sync/README.md`: how every stage works and why.

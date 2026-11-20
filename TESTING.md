# Testing Doc Sync

Doc Sync takes a shipped product change, described as a Jira-style ticket,
finds the live Document360 articles it has made wrong, and drafts the fixes,
including flagging outdated screenshots. This guide gets you from the zip to
your first run. For how the pipeline works in detail, see
[doc_sync/README.md](doc_sync/README.md).

## What you need

- A Mac with Python 3.9 or later (`python3 --version`).
- Claude Code installed and logged in. The pipeline runs every model call
  through your Claude Code login. No API key needed.
- Homebrew, to install Tesseract (used to read text in screenshots).

## Set up (once, about 10 minutes)

Run everything from the unzipped `Doc360/` folder.

1. **Rebuild the Python environment.** The `.venv` folder in the zip only
   works on the machine it was made on.

   ```
   rm -rf .venv
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   ```

2. **Install Tesseract.**

   ```
   brew install tesseract
   ```

3. **Set your own Document360 user ID.** Open `.env` and replace the value of
   `D360_USER_ID` with yours (ask Diya if you don't know it). Drafts and
   screenshot uploads are attributed to this user. Leave the other values as
   they are.

4. **Check that it works.**

   ```
   .venv/bin/python doc_sync/claude_call.py selftest
   .venv/bin/python doc_sync/kb_index.py status
   ```

   The first command should print a short answer from Claude. The second shows
   the age of the knowledge index (the local copy of all six live workspaces
   that discovery searches). The zip includes an index built on 2026-11-20.

Always use `.venv/bin/python`, never plain `python3`. The system Python
doesn't have the packages and fails on the first import. A `NotOpenSSLWarning`
on every command is harmless.

## Run a ticket

1. Open the `Doc360/` folder in Claude Code.
2. Type `/doc-sync`.
3. Answer its questions: the ticket summary, the description, the product lines
   (optional), the old wording the product used before the change, any PRD or
   product note PDFs, and your name.
4. The skill walks the ticket through To Do, In Draft, Peer review, and For
   review, and then publishes a Jira-style page with the plan, the drafts, and
   the screenshot review.

If the index is more than 48 hours old, the skill offers to rebuild it. You can
say no and test on the index as it is. A rebuild takes about 30 minutes and
only reads from Document360.

**Pick a real change you know well.** You'll judge the results better when you
already know which articles it should affect.

## What it writes, and where

| Where | What happens |
|---|---|
| Live articles (the six product workspaces) | Read only. Doc Sync never writes to a live article during a ticket run. |
| Archived workspace | Phase 2 overwrites the Archived articles whose links you give it, with no undo. It asks you to confirm each one first. |
| Document360 Drive (the I2P agent's folder) | Retake screenshots you supply are uploaded here. |
| Your machine | Everything else: `doc_sync/runs/<run name>/` holds the ticket, the plan, the drafts, and a log of every step. |

**Use your own Archived scratch articles.** Create a few blank articles in the
Archived workspace for yourself. Never give the pipeline links to articles
someone else is using, and never links to live articles.

## Screenshots

In phase 2, every screenshot in an approved article is reviewed and marked
**fine**, **unsure** (check it in the product), or **stale** (with instructions
for the retake). When another article already shows the new UI, the pipeline
may reuse that screenshot and mark it for you to confirm.

To supply retakes, capture them with the I2P extension (Free Capture, and then
Download all) and save each one as
`doc_sync/runs/<run name>/screenshots/<plan #>/<image #>.png`. Then ask Claude
Code to run the screenshots step. Run it with `--check-only` first to check the
files without uploading anything.

**This step hasn't been tested live yet.** If you get as far as retakes, please
try it and report what happens. It's the most useful test you can do.

## What to look for

- **Discovery:** articles it missed, and articles it flagged that the change
  doesn't affect.
- **Drafts:** edits that are wrong, unsupported by the ticket, or that change
  things they shouldn't.
- **Screenshots:** stale screenshots marked fine, fine ones marked stale, and
  unclear retake instructions.
- **Anything that breaks:** errors, hangs, or steps that confused you.

## Reporting

Send Diya:

- The run name.
- What you expected and what happened.
- The run folder, `doc_sync/runs/<run name>/`, zipped. It holds everything
  needed to see what the pipeline did.

## Known limits

- The index is a snapshot. Articles changed after it was built aren't seen
  until it's rebuilt.
- A full run uses your Claude Code usage. Phase 2 on articles with many
  screenshots can take 10 minutes or more.
- The live retake leg (upload, swap, and draft rewrite) is untested, as noted
  above.

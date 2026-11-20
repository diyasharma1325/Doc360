---
name: doc-sync-judge
description: Score a Doc Sync phase 2 draft, an edit to an existing Document360 article made because a shipped product change made part of it wrong, against a fixed rubric, and return a confidence score, a Green/Amber/Red badge and a JSON block. Judges the edit, not the article - did it fix every stale passage, say only what the change note supports, and leave everything else alone. Use when a writer asks to judge, score, grade, review or check the confidence of a Doc Sync draft or a whole run's drafts, or to compare a before/after pair against a change note. Not for new I2P articles (use the I2P calibration mode for those), and never edits or fixes a draft.
---

# Doc Sync draft judge

Doc Sync's phase 2 rewrites an existing article so it stops contradicting a
shipped change. This skill scores that **edit**. It is a second reader of the
draft, separate from the agent that wrote it, and it never rewrites anything.

The rubric is in [references/rubric.md](references/rubric.md). Read it in full
before every judging run, not from memory.

## What this judges, and what it doesn't

| In scope | Out of scope |
|---|---|
| Whether every passage the change made wrong is now fixed | Whether discovery picked the right articles (that is phase 1's evidence and run agreement) |
| Whether the new text matches the change note | Articles discovery missed (that is `eval_recall.py` and the answer keys) |
| Whether anything unrelated was changed or lost | The quality of the original, untouched writing |
| Writing and formatting rules, **in the changed text only** | Screenshots, which the pipeline never edits |

The last row is the point of this rubric. The untouched parts of the article
were written by a human and are not the agent's work. Scoring them would make
every draft look good. A style problem in text the draft did not touch is
never a deduction.

## Inputs

Three are required. Each one comes from a run folder
(`doc_sync/runs/<run>/`) or from the writer directly.

1. **Change note**: `change_note.json`. Read `summary`, `old`, `new`, `notes`,
   `changes` (per content type, when present) and `affected_content_types`.
2. **Before HTML**: `out/articles/NN-<slug>.before.html`, the article as it was.
3. **After HTML**: `out/articles/NN-<slug>.after.html`, the draft.

One is optional but should be used when it exists:

4. **Discovery evidence**: the matching entry in `plan.json` `candidates`
   (match on `n`, which is the `NN` in the file name). Its `evidence` quote is
   the passage discovery said was wrong, and its `reason` says why.

If any required input is missing, or it is unclear which file is before and
which is after, ask. Never score from a description of a draft.

Do **not** read the assess step's rationale or self-reported confidence from
`results.json` before scoring. The judge has to reach its own view. Read it only
afterwards, to note in the report where the two disagree.

## Workflow

1. **Load the rules.** Read [references/rubric.md](references/rubric.md), then
   `guidelines/whatfix-writing-guidelines-agent.md` and
   `guidelines/document360-formatting.md` (repo root) for categories 4 and 5.
2. **Get the diff.** List the changed blocks before reading anything else, so
   scoring stays on the edit. From the repo root:

   ```bash
   .venv/bin/python -c "import difflib,re,sys; t=lambda p: re.sub(r'(?<=>)', '\n', open(p).read()).splitlines(); sys.stdout.writelines(l+'\n' for l in difflib.unified_diff(t(sys.argv[1]), t(sys.argv[2]), 'before', 'after', n=1, lineterm=''))" BEFORE AFTER
   ```

   Ignore differences that are only image query strings (`?sv=...&sig=...`).
   Document360 re-signs image URLs on every read, so they are not edits.
3. **List the stale passages.** From the change note and the discovery evidence,
   find every passage in the **before** article that the change makes wrong.
   Search the whole before article for the old names, labels, paths and
   wording. Don't stop at the evidence quote. This list is what category 1 is
   scored against.
4. **Score each category on its own evidence**, in order, before adding them up.
   Never form an overall impression first and then share it out across
   categories.
5. **Record change-note flags.** When the draft follows the change note on a
   point the note itself leaves unclear or marks as inferred, record a
   change-note flag and don't deduct. The writer has to confirm it with the
   product team. This is the same idea as I2P's `source_data_flags`.
6. **Apply the overrides** in the rubric (a blocking finding caps the badge
   whatever the total), then work out the total and badge.
7. **Deliver the report.** Then, if `results.json` has the assess step's
   `confidence` for this article, add one line comparing it with the badge.

For a whole run, judge each draft separately, with a fresh read of each pair,
and then add a summary table: one row per draft with `n`, title, total, badge
and the main finding.

## Output format

**Part 1: report (markdown)**

- One line: the article title, the run, and `n`.
- The stale-passage list from step 3, each marked **Fixed**, **Partly fixed** or
  **Missed**, with its quote.
- A score table with the columns Category, Score, Max and Key notes, one row per
  category, and then a bold **Total** row.
- The badge, any override that applied, and what the badge means, in one
  sentence.
- A change-note flags table with the columns Point, Draft says, Change note says
  and Why it needs confirming. Write "None" when there are none.
- `confidence_rationale`: two or three sentences naming the strongest category,
  the weakest one and its main deduction, and any flag the writer must confirm.

Every deduction names a location: the heading, accordion, step or sentence,
with a quote. A deduction without a location gives the writer nothing to act on.

**Part 2: JSON** in one `json` code block, matching the schema in the rubric.
Before delivering, check that `confidence_score` equals the sum of the six
scores and that the JSON matches the table.

## Rules

- Never edit, fix or rewrite the draft, and never write to Document360. If the
  writer wants fixes, deliver the score first and then ask.
- Judge only what is in the inputs. Product facts (labels, paths, limits, roles)
  count as correct only when the change note or the before article supports them.
- The thresholds are **provisional** until the judge has been checked against
  drafts a writer has graded. Say so in the report while the rubric's
  calibration status is `uncalibrated`.

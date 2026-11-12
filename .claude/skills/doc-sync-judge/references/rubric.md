# Doc Sync draft rubric

**Calibration status: `uncalibrated`.** The weights and badge thresholds are a
first proposal. Change this to `calibrated (date, n drafts)` after the judge's
scores have been compared with a writer's grades on about 20 drafts, and the
thresholds adjusted to match.

Used only by the `doc-sync-judge` skill. Adapted from the I2P calibration rubric:
same scoring method (separate categories, a cited location for every deduction,
flags kept out of the score, Green/Amber/Red), with categories rebuilt for an
**edit** rather than a new article.

---

## Governing principle

The judge scores **the edit**, not the article.

Every category asks the same question: **does the draft make the article
accurate for this change, without damaging anything else?**

Text the draft did not touch is the human author's, and is never scored for
style, structure or examples. The only exception is category 1: untouched text
that is still wrong because of the change is a missed fix.

How the draft fixes something is not scored, only whether it does. A reworded
sentence, a new sentence and a removed sentence can all be correct fixes.

---

## Category weights

| # | Category | Max | JSON key |
|---|---|---|---|
| 1 | Change coverage | 30 | `change_coverage` |
| 2 | Accuracy to the change | 25 | `change_accuracy` |
| 3 | Preservation | 20 | `preservation` |
| 4 | Writing rules (changed text) | 10 | `writing_rules` |
| 5 | Callouts and formatting (changed text) | 10 | `callouts_formatting` |
| 6 | Fit with the article | 5 | `article_fit` |
| | **Total** | **100** | |

Categories 1 to 3 carry 75 points because their failures mislead readers or
break the article. Failures in categories 4 to 6 are ones a reviewing writer
catches anyway.

---

## Category 1: Change coverage (0–30)

**The question:** is every passage that the change made wrong now fixed?

Score against the stale-passage list (SKILL.md, workflow step 3), not only
against the discovery evidence. Count passages in every place they can appear:
body text, steps, headings, accordion titles, table cells, callouts, link text,
image alt text, glossary entries and "see also" lines.

A passage is:
- **Fixed** when it no longer says anything the change made wrong.
- **Partly fixed** when part of it is still wrong. For example, the step is
  updated but its Note still names the old label.
- **Missed** when it is unchanged and still wrong.

| Score | Descriptor |
|---|---|
| 26–30 | Every stale passage fixed, including the easily missed ones (headings, alt text, link text, cross-references). |
| 18–25 | All main passages fixed; one minor passage partly fixed or missed, such as a passing mention or a link's text. |
| 9–17 | A passage a reader would act on (a step, a navigation path, a feature description) is missed or only partly fixed. |
| 0–8 | Several stale passages missed, or the evidence passage itself is not fixed. |

**Overrides:** if the discovery evidence passage is **Missed**, the badge is
Red. If any other passage is **Missed** or **Partly fixed**, the badge is at
most Amber. A draft that leaves something wrong is never Green.

---

## Category 2: Accuracy to the change (0–25)

**The question:** does the new text say what the change note says, and no more?

Check every changed sentence:
- Does it match the change note's `new` state (and the matching `changes` entry
  for that content type)?
- Is each product fact it adds (UI label, menu path, button name, limit, role,
  stage, product line, Beta or GA status) supported by the change note or the
  before article? A fact with no support is **invented**, even when it sounds
  plausible.
- Does it overstate the change? For example, the note covers DAP for Web and the
  draft says "on all platforms", or the note says "moved" and the draft says
  "removed".

When the draft follows the change note on a point the note itself marks as
unclear or inferred (its `notes` field, or wording like "etc." or
"respectively"), that is a **change-note flag**, not a deduction.

| Score | Descriptor |
|---|---|
| 22–25 | Every changed sentence matches the change note. No invented facts. Scope stated exactly as the note gives it. |
| 15–21 | One imprecise statement that is not wrong, such as a vague phrase where the note gives a specific label. |
| 7–14 | One statement that contradicts the note or overstates its scope, or one invented product fact. |
| 0–6 | Several contradictions or invented facts, or the edit describes a different change. |

**Override:** any invented product fact caps the badge at Amber.

---

## Category 3: Preservation (0–20)

**The question:** was everything the change did not affect left as it was?

Check the diff for:
- **Unrelated rewording**: sentences changed that have nothing to do with the
  change. Fixing a typo or a style rule in untouched text counts as unrelated.
  The assess prompt tells the agent not to.
- **Lost content**: paragraphs, steps, list items, callouts, table rows, links or
  images removed without the change requiring it.
- **Structural damage**: accordions, tables, tabs, lists or callouts broken,
  merged, reordered or unwrapped; mismatched tags; block IDs changed on blocks
  that weren't edited.
- **Removed content that the change does require**: this is correct and is not a
  deduction. For example, deleting a step for a feature that no longer exists.

Image URLs that differ only in their query string are not edits.

| Score | Descriptor |
|---|---|
| 18–20 | Only change-related passages differ. Structure, links and images intact. |
| 12–17 | One small unrelated edit, such as a reworded sentence or a fixed typo, with no loss of meaning. |
| 5–11 | Unrelated content lost or rewritten in a way that changes meaning, or one structural element damaged. |
| 0–4 | Widespread unrelated changes, or the article's structure is broken. |

**Override:** broken HTML, or a lost section unrelated to the change, makes the
badge Red.

---

## Category 4: Writing rules, changed text only (0–10)

**The question:** does the new and changed text follow
`guidelines/whatfix-writing-guidelines-agent.md`?

Check only sentences the draft added or changed. The rules most often broken in
an edit:
- Active voice, present simple tense, under 30 words, one idea per sentence.
- Words to avoid replaced (allows/lets, navigate, via, click on, may, end users,
  popup, "you can" as a step opener).
- No em dashes, semicolons, exclamation marks or stray parentheses.
- Steps are complete imperative sentences ending in a period, one action each.
- UI element, stage and role names bold in body text, but never in headings.
- A new list or table has an introducing sentence. No single-item list.
- No "this change" without stating what changed.

| Score | Descriptor |
|---|---|
| 9–10 | No violations in the changed text. |
| 6–8 | One or two minor violations. |
| 3–5 | Several violations, or one that makes a step unclear. |
| 0–2 | The changed text largely ignores the guidelines. |

---

## Category 5: Callouts and formatting, changed text only (0–10)

**The question:** is the changed text marked up correctly, and does the change
bring in a callout it needs?

Check against `guidelines/document360-formatting.md`:
- **Callout needed by the change**: a new limitation, gating rule, irreversible
  action, default or propagation delay goes in a Note. Non-blocking clarification
  goes in an Info. A Tip appears only in a Best Practices article.
- **Callout type**: a changed callout still has the right type for its content.
- **Markup**: new elements use the reference's HTML (callout `blockquote`
  classes, accordion `details`/`summary`, list and table markup). No markdown,
  no `<h1>`, no `<em>`. No two callouts of the same type back to back.
- **Links**: a changed or new link is relative, uses the right project prefix and
  has `target="_blank"`. A link to an article the change archives is repointed or
  removed.

| Score | Descriptor |
|---|---|
| 9–10 | Any callout the change needs is present and correctly typed. Markup and links correct. |
| 6–8 | One callout of the wrong type, or one markup or link issue. |
| 3–5 | A Note the change needs is missing, or several markup issues. |
| 0–2 | Changed text badly marked up, or markdown in the HTML. |

---

## Category 6: Fit with the article (0–5)

**The question:** does the changed text read as part of the article?

- The feature's terms match the rest of the article after the edit. One section
  doesn't say the new name while the next still uses a synonym of the old one,
  where that isn't already a category 1 miss.
- Lead-ins, counts and summaries still match what follows. For example, "the
  following three options" when the list now has two.
- An opener or overview line that summarises the article still describes it.

| Score | Descriptor |
|---|---|
| 5 | Changed text fits; counts, lead-ins and summaries all still true. |
| 3–4 | One inconsistency a reader would notice. |
| 0–2 | The edit leaves the article contradicting itself. |

---

## Overrides

Apply these after adding up the total. A blocking finding is never averaged away
by high scores elsewhere.

| Finding | Effect |
|---|---|
| Discovery evidence passage Missed (category 1) | Badge Red |
| Any other stale passage Missed or Partly fixed (category 1) | Badge at most Amber |
| Broken HTML, or a lost section unrelated to the change (category 3) | Badge Red |
| Any invented product fact (category 2) | Badge at most Amber |
| Any change-note flag | Badge unchanged, but the report says the writer must confirm the flags before publishing |

---

## Badge thresholds (provisional)

| Score | Badge | Meaning |
|---|---|---|
| 85–100 | Green | The edit is accurate and contained. A quick read and the flags, if any, are all that remain. |
| 65–84 | Amber | Targeted rework needed: a passage missed, an imprecise statement, or an unrelated edit to undo. |
| Below 65 | Red | Don't publish as is. The edit misses the change, damages the article, or says something unsupported. |

---

## Worked example (illustrative)

This example shows the standard of evidence expected. It is not a real judged
run.

**Change:** AI Pop-ups are removed from DAP for Web. **Article:** Pop-ups Best
Practices. **Discovery evidence:** "You also have the option to create Pop-ups
using AI. For more information, see Create AI Pop-ups."

Stale passages:

| # | Passage | Status |
|---|---|---|
| 1 | Intro: "You also have the option to create Pop-ups using AI. For more information, see Create AI Pop-ups." | Fixed: sentence and link removed |
| 2 | Accordion "Keep Pop-ups short": "Use the AI generated image toggle to add visuals." | Missed |

| Category | Score | Max | Key notes |
|---|---|---|---|
| 1 Change coverage | 20 | 30 | Evidence passage fixed. The AI image toggle in "Keep Pop-ups short" is untouched. |
| 2 Accuracy to the change | 25 | 25 | Removal only. No new claims. |
| 3 Preservation | 17 | 20 | Draft also changed "popups" to "Pop-ups" in two untouched paragraphs, which is unrelated. |
| 4 Writing rules | 10 | 10 | No changed sentences other than a deletion. |
| 5 Callouts and formatting | 10 | 10 | Intro paragraph markup intact after the deletion. |
| 6 Fit with the article | 5 | 5 | Intro still reads correctly. |
| **Total** | **87** | **100** | |

Overrides applied: stale passage 2 Missed, so the badge is at most Amber.

Badge: **Amber**. The total of 87 alone would be Green, but the draft still
tells readers to use a toggle that no longer exists. The writer has one line to
fix and two unrelated spelling changes to undo. Had passage 1, the evidence
quote, been the one missed, the badge would be Red.

---

## JSON schema

```json
{
  "run": "ai-popups-e2e",
  "n": 3,
  "article_id": "",
  "title": "",
  "stale_passages": [
    { "passage": "quote", "location": "heading/accordion/step", "status": "Fixed | Partly fixed | Missed" }
  ],
  "rubric_scores": {
    "change_coverage":     { "score": 0, "max": 30, "rationale": "1 sentence" },
    "change_accuracy":     { "score": 0, "max": 25, "rationale": "1 sentence" },
    "preservation":        { "score": 0, "max": 20, "rationale": "1 sentence" },
    "writing_rules":       { "score": 0, "max": 10, "rationale": "1 sentence" },
    "callouts_formatting": { "score": 0, "max": 10, "rationale": "1 sentence" },
    "article_fit":         { "score": 0, "max": 5,  "rationale": "1 sentence" }
  },
  "confidence_score": 0,
  "overrides_applied": [],
  "badge": "Green | Amber | Red",
  "calibration_status": "uncalibrated",
  "confidence_rationale": "2 to 3 sentences",
  "change_note_flags": [
    { "point": "", "draft_says": "", "change_note_says": "", "why": "" }
  ],
  "assess_confidence": "high | medium | low | null"
}
```

`confidence_score` must equal the sum of the six `score` values. `badge` is the
threshold band for that total, then adjusted by `overrides_applied`.

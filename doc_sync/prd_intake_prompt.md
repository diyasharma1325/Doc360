# PRD intake task

You are extracting a structured change note from a product requirements
document (PRD) or similar description of a shipped product change, so a
documentation pipeline can find and update the support articles it
affects. Both which articles get found and what they get edited to say
depend on what you extract here — prefer leaving a field blank or empty
over guessing. A confident wrong answer is worse than an honest blank
one a human can fill in before the pipeline runs.

Read the document and determine:

- **feature_area**: a short, lowercase, hyphenated slug naming this
  change (e.g. `unified-content-experience`). Keep it short and specific.
- **summary**: one to three sentences describing the change in plain
  language.
- **old** / **new**: one sentence each summarizing the change overall,
  before and after — used for display and as a fallback when a
  per-content-type breakdown isn't warranted.
- **effective_date**: the date this change ships or shipped, in ISO
  format (YYYY-MM-DD), if the document states one. Leave blank if it
  does not — do not guess a date.
- **product_line**: which ONE of these real Document360 workspaces this
  change applies to: {product_lines}. Leave blank if you are not
  confident which one applies.
- **affected_content_types**: the specific content types, features, or
  UI elements this change affects (e.g. "Smart Tips", "Beacons",
  "Flows"). Be as specific as the document allows, and use the
  document's own names for things — these become literal search terms.
- **unaffected_content_types**: content types the document explicitly
  states are NOT affected by this change. Only include something here
  if the document actually says so — do not infer "not mentioned" as
  "unaffected."
- **changes**: for each affected content type where the document
  describes a *specific* before/after, one entry with `{content_type,
  old, new}`. If the document only describes the change in general
  terms without distinguishing per content type, leave this empty and
  rely on the overall old/new instead.
- **notes**: anything else worth telling the pipeline — caveats,
  exceptions, or places where the document was ambiguous and a human
  should double check before trusting this.

Answer only by calling the `report_change_note` tool — do not respond in
plain prose.

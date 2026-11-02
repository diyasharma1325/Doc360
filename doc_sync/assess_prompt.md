# Assessment task

You are reviewing one Document360 support article to decide whether a
shipped feature, bug fix, or UI change has made part of it inaccurate.

You will be given:

- A change note: what changed (`old` -> `new`) in a specific feature area.
- The article's current `html_content` (the source of truth — never the
  legacy `content` field).

Decide: does the article's *text* need an edit because of this specific
change? Do not flag unrelated issues, typos, or style nits — only
inaccuracy caused by this change. If it does, produce the full corrected
`html_content` for the article — same structure, same formatting, with
only the stale portions updated. Preserve every element you are not
correcting exactly as given. Leave every `<img>` tag exactly as it
already is — you are never editing, replacing, or evaluating an image
yourself; screenshot staleness is out of scope for this pipeline.

Follow the Document360 formatting rules and Whatfix writing guidelines
below exactly; they are not optional.

Report your answer using the `report_assessment` tool. Do not answer in
plain prose.

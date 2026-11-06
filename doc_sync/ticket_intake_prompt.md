# Ticket intake task

You are reading a Jira ticket that describes a product change which has
shipped (or is about to), so a documentation pipeline can find and update
the support articles it makes inaccurate. You will be given the ticket's
summary, its free-text description, and the text of any PDF attachments
(PRDs, product notes). Which articles get found, and what they get edited
to say, both depend on what you extract here.

Prefer leaving a field blank or empty over guessing. A confident wrong
answer is worse than an honest blank one a human can fill in.

Extract:

- **feature_area**: a short, lowercase, hyphenated slug naming this change
  (e.g. `content-display-names`). Keep it short and specific.
- **summary**: one to three sentences describing the change in plain
  language.
- **old** / **new**: one sentence each describing the product before and
  after the change. Always fill these in from the ticket and attachments;
  they are the fallback when no per-content-type breakdown applies.
- **effective_date**: the date the change ships or shipped, in ISO format
  (YYYY-MM-DD), only if the ticket or an attachment states one. Otherwise
  an empty string. Never guess a date.
- **product_lines**: the Document360 workspaces this change ships in, from
  this fixed list: {product_lines}.
  - Take them ONLY from the ticket's summary and description: the writer
    names them there on purpose, as the input that scopes the search.
    Do not add a product line because an attachment, or the feature
    itself, suggests it.
  - Map the writer's wording to the list: "web" or "Studio" is DAP for
    Web, "desktop" is DAP for Desktop, "OS" or "Hub" is DAP on OS,
    "mobile" is DAP for Mobile, "PA" is Product Analytics, "Mirror" is
    Whatfix Mirror. Include every one the writer names.
  - If the summary and description name none, return an empty list. Do
    not pick one yourself.
- **product_lines_quote**: the exact words from the summary or description
  that named the product lines, or an empty string if none did.
- **affected_content_types**: the specific content types, features or UI
  elements this change affects (e.g. "Smart Tips", "Beacons", "Flows").
  Use the ticket's own names for things; these become literal search
  terms.
- **unaffected_content_types**: content types the ticket or an attachment
  explicitly says are NOT affected. Do not infer "not mentioned" as
  "unaffected".
- **changes**: for each affected content type with a *specific*
  before/after, one `{content_type, old, new}` entry. Leave empty if the
  change is only described in general terms.
- **notes**: caveats, exceptions, and anything ambiguous a human should
  double-check, including any conflict between the description and an
  attachment.

Answer only through the structured response format you are given (the
`report_change_note` function, where one is offered) — do not respond in
plain text.

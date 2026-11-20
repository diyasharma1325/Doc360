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
    not pick one yourself here; that is what **predicted_product_lines**
    is for.
  - If the request has a "Product lines (set on the ticket)" line, the
    ticket's creator chose them: return exactly those.
- **product_lines_quote**: the exact words from the summary or description
  that named the product lines, or an empty string if none did.
- **predicted_product_lines**: ONLY when product_lines is empty and the
  request has no "Product lines (set on the ticket)" line; otherwise an
  empty list. Your best prediction, from the same fixed list, of the
  workspaces this change ships in. A writer confirms or corrects it
  before any search runs. Use the whole ticket, attachments included:
  - an attachment or the description naming a platform or surface
    ("browser extension", "desktop app", "iOS", "Studio");
  - a feature that exists in only one product (for example Funnel or
    Trend Insights are Product Analytics; Simulations are Whatfix
    Mirror);
  - otherwise, the product lines the feature is generally part of.
  Include only lines you have a concrete reason for, fewest first; do
  not list all six to be safe. Return an empty list if nothing in the
  ticket gives you a reason.
- **prediction_basis**: one short sentence on why you predicted those
  product lines, citing the ticket or attachment wording you used. An
  empty string when predicted_product_lines is empty.
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
- **old_terms**: the words the product used for the OLD state that this
  change replaces: tab, page, section, menu, button or setting names
  (e.g. "Widgets page", "Display Rules"). Outdated articles still use
  these words, so they are what finds them. Take them ONLY from what the
  ticket or an attachment says about the old state; return an empty
  list if it doesn't say. Never guess here: a separate step suggests old
  terms for the writer to confirm when the ticket gives none.
- **ui_facts**: short, plain statements of what the product's UI looks
  like AFTER the change, as the ticket or an attachment states it: where
  things now live, what each renamed or moved element is called now, and
  what explicitly STAYS the same (e.g. "Smart Tips, Beacons, Launchers and
  Blockers are listed under the Content tab in the Dashboard nav", "The
  Widgets entry stays in the nav for Pop-ups, Self Help and Task List").
  One fact per item. Screenshots are judged against these, so never guess:
  return an empty list if the ticket doesn't say.
- **notes**: caveats, exceptions, and anything ambiguous a human should
  double-check, including any conflict between the description and an
  attachment.

Answer only through the structured response format you are given (the
`report_change_note` function, where one is offered) — do not respond in
plain text.

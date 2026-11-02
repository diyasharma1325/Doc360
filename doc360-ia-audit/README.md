# Document360 IA Audit

Audits your Document360 workspace's category/article structure and flags
maintenance candidates. Read-only — it never writes anything back to
Document360.

## What it checks (v1)

1. **Empty categories** — no articles, no subcategories. Dead-end nav nodes.
2. **Single-article categories** — likely over-fragmented; could probably
   fold into a sibling or parent.
3. **Exact duplicate titles** — same title used more than once.
4. **Near-duplicate titles** — similar but not identical titles (catches
   things like "What is Whatfix" vs "What is Whatfix?" living in two
   different categories).
5. **Stale published articles** — live content untouched for N+ months
   (default 6).
6. **Stuck drafts** — drafts untouched for N+ months. Either finish or
   archive them.
7. **Max-depth categories** — Document360 caps nesting at 3 levels; these
   are already at the ceiling.

Every finding is also exported to a CSV so you can filter/sort/assign it
in Excel or Sheets.

## Setup

```bash
pip install requests
```

## Get your API token

Document360 portal → **Settings → Knowledge base portal → API tokens**.
Needs at least read access to the workspace you want audited.

## Run it

```bash
export DOC360_API_TOKEN="your-token-here"
python3 audit.py
```

Optional flags:

```bash
python3 audit.py --stale-months 9          # change the staleness threshold
python3 audit.py --version-id <uuid>       # audit a specific workspace/version instead of the main one
python3 audit.py --out my_report.md --csv-out my_flagged.csv
```

## Output

- `document360_audit_report.md` — a readable summary, ready to paste into
  Confluence or drop into a ticket.
- `document360_audit_flagged.csv` — every flagged item as a row, for
  triage in a spreadsheet.

## Notes / limitations (be upfront about these)

- This only looks at **structure and metadata** (titles, dates, category
  shape) — it doesn't read article body content, so it won't catch things
  like broken internal links or screenshot/text mismatches. That's a
  natural v2 (the earlier "screenshot drift checker" idea would plug in
  here using the per-article content fetch).
- "Near-duplicate" is a simple string-similarity check on titles only —
  it will flag some false positives (e.g. "Create a Flow" vs "Create a
  Task List" if your threshold is too loose). Treat it as a shortlist to
  eyeball, not a verdict.
- Staleness is based on `modified_at`, which only reflects edits made
  *through Document360* — a correct-but-untouched article isn't
  necessarily wrong, it's just a candidate worth a second look.
- Rate limits: the whole workspace tree is fetched in a single API call,
  so this is light on quota even for large knowledge bases.

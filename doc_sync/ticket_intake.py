"""Stage 1 (intake) for a ticket run: the simulated Jira ticket's summary,
free-text description and PDF attachments -> a structured change note, in
one Claude call.

This is the writer moving the ticket from To Do to In Draft. The product
lines decide which workspaces discovery searches. They come from, in order
(2026-11-15):

1. The ticket's product lines FIELD, when its creator set one
   (`ticket.py new --product-lines`). Used exactly as given; nothing is
   predicted, so the creator's choice is never second-guessed.
2. Otherwise, the product lines the summary or description NAMES, which
   the model maps onto the six live workspaces.
3. Otherwise, the model's PREDICTION, from the whole ticket, attachments
   included. It comes from the same intake call (two extra schema fields,
   no extra model call), and a comment asks the writer to confirm or
   override it before phase 1 (`ticket_run.py phase1 --product-lines`).

A ticket with none of the three is bounced, as the I2P agent bounces a
ticket with missing inputs: a comment saying what to add, the ticket moved
back to To Do, and no change note saved. Fix the ticket
(`ticket.py update`) and run intake again.

If the model call itself fails, the same happens with an "intake failed"
comment, so the ticket is never left in In Draft with no change note.

The model's product lines are checked again in code against
core/workspaces.py's allow-list, so a name outside the six can never reach
discovery.

Attachments are read as text first (pdf_text.py). One that can't be read
(too big, too long, not a PDF, a scanned image) does not stop the run; it
is recorded on the ticket as a comment, so nobody assumes it was used.

OLD WORDING (2026-11-09). Outdated articles describe the old state in the
old words, so those words are what discovery searches for. Intake takes
them from the ticket (`old_terms`); when the ticket gives none, a second,
small model call suggests some from the product reference for the
ticket's product lines (`old_terms_suggested`), and a comment shows them
to the writer to confirm or correct (`ticket_run.py replan --old-terms`).
A failed suggestion call never stops intake.

    python3 doc_sync/ticket_intake.py <run>
"""
import argparse
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR.parent / "core"))  # workspaces.py lives in ../core

from dotenv import load_dotenv

# Other modules get .env loaded as a side effect of importing d360_client;
# intake never touches Document360.
load_dotenv(THIS_DIR.parent / ".env")

import claude_call
import pdf_text
import product_context
import ticket
import workspaces
from change_note import ChangeNote, ContentChange, save_change_note

PROMPT_PATH = THIS_DIR / "prompts" / "ticket_intake.md"
OLD_TERMS_PROMPT_PATH = THIS_DIR / "prompts" / "old_terms.md"
# The suggestion call carries the product reference for the ticket's lines
# up to this size (all four DAP surfaces: ~105 KB; all six: ~180 KB).
OLD_TERMS_CONTEXT_MAX_BYTES = 120_000
MAX_OUTPUT_TOKENS = 8192
# Per attachment. A 300-page PRD is far more than intake needs to describe a
# change; the cut is said in the request, so the model knows it saw a part.
MAX_ATTACHMENT_CHARS = 120_000

INTAKE_SCHEMA = {
    "type": "object",
    "properties": {
        "feature_area": {"type": "string"},
        "summary": {"type": "string"},
        "old": {"type": "string"},
        "new": {"type": "string"},
        "effective_date": {"type": "string", "description": "ISO date, or empty string if not stated."},
        "product_lines": {
            "type": "array",
            "items": {"type": "string", "enum": workspaces.names()},
            "description": "Workspaces the ticket's summary or description names. Empty if none.",
        },
        "product_lines_quote": {"type": "string"},
        "predicted_product_lines": {
            "type": "array",
            "items": {"type": "string", "enum": workspaces.names()},
            "description": "Only when the ticket names no product line: the predicted workspaces. Else empty.",
        },
        "prediction_basis": {"type": "string"},
        "affected_content_types": {"type": "array", "items": {"type": "string"}},
        "unaffected_content_types": {"type": "array", "items": {"type": "string"}},
        "changes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "content_type": {"type": "string"},
                    "old": {"type": "string"},
                    "new": {"type": "string"},
                },
                "required": ["content_type", "old", "new"],
            },
        },
        "old_terms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Names the ticket or an attachment gives for the old state. Empty if it gives none.",
        },
        "notes": {"type": "string"},
    },
    "required": [
        "feature_area", "summary", "old", "new", "effective_date", "product_lines",
        "product_lines_quote", "predicted_product_lines", "prediction_basis", "affected_content_types", "unaffected_content_types",
        "changes", "old_terms", "notes",
    ],
}

OLD_TERMS_SCHEMA = {
    "type": "object",
    "properties": {
        "terms": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "basis": {"type": "string", "description": "Where it came from, in a short phrase."},
                },
                "required": ["term", "basis"],
            },
        },
    },
    "required": ["terms"],
}


class IntakeRefused(RuntimeError):
    """The run is not in a state where intake may run (e.g. already done)."""


def _system_prompt():
    return PROMPT_PATH.read_text().replace("{product_lines}", ", ".join(workspaces.names()))


def _request(tk, attachments):
    lines = [
        f"Ticket {tk['key']}",
        f"Summary: {tk['summary']}",
    ]
    if tk.get("product_lines"):
        lines.append(f"Product lines (set on the ticket): {', '.join(tk['product_lines'])}")
    lines += [
        "Description:",
        tk.get("description") or "(empty)",
    ]
    for i, a in enumerate(attachments, 1):
        text = a["text"]
        cut = ""
        if len(text) > MAX_ATTACHMENT_CHARS:
            text = text[:MAX_ATTACHMENT_CHARS]
            cut = f" (first {MAX_ATTACHMENT_CHARS:,} characters only)"
        lines += ["", f"Attachment {i}: {a['name']}, {a['pages']} page(s){cut}", text]
    return "\n".join(lines)


def _extract(system, request):
    return claude_call.generate(system=system, user=request, schema=INTAKE_SCHEMA,
                                label="ticket intake", max_tokens=MAX_OUTPUT_TOKENS)


def _clean_terms(terms):
    out = []
    for t in terms or []:
        t = " ".join(str(t).split())
        if t and t.lower() not in [o.lower() for o in out]:
            out.append(t)
    return out


def _suggest_old_terms(request, result, product_lines):
    """Old terms suggested from the product reference for `product_lines`,
    as [{term, basis}], for a ticket that stated none."""
    files = product_context.files_for_lines(product_lines)
    parts = product_context.prompt_parts_for_lines(product_lines) \
        if product_context.size_of(files) <= OLD_TERMS_CONTEXT_MAX_BYTES else []
    system = OLD_TERMS_PROMPT_PATH.read_text() + "".join(parts)
    user = "\n".join([
        request,
        "",
        "What intake extracted:",
        f"- summary: {result.get('summary', '')}",
        f"- old: {result.get('old', '')}",
        f"- new: {result.get('new', '')}",
        f"- affected: {', '.join(result.get('affected_content_types') or [])}",
    ])
    answer = claude_call.generate(system=system, user=user, schema=OLD_TERMS_SCHEMA,
                                  label="old terms", max_tokens=2048)
    seen, out = set(), []
    for t in answer.get("terms") or []:
        term = " ".join((t.get("term") or "").split())
        if term and term.lower() not in seen:
            seen.add(term.lower())
            out.append({"term": term, "basis": (t.get("basis") or "").strip()})
    return out[:6]


def _old_terms_comment(stated, suggested, error=None):
    if stated:
        return ("I'll search for articles that still use the old wording from the ticket: "
                + ", ".join(f"**{t}**" for t in stated) + ".")
    lines = ["The ticket doesn't say what the product called this **before** the change. Outdated "
             "articles still use the old words, so they're what finds them."]
    if suggested:
        lines += ["", "I'll also search for these old terms, **suggested** from the product reference. "
                  "Please confirm or correct them:", ""]
        lines += [f"- **{s['term']}** ({s['basis']})" if s.get("basis") else f"- **{s['term']}**"
                  for s in suggested]
    elif error:
        lines += ["", f"I couldn't suggest any (`{error}`)."]
    else:
        lines += ["", "I couldn't find any in the product reference either."]
    lines += ["", "To correct them, reply on the plan with the old terms, and the next re-plan "
              "searches for those instead."]
    return "\n".join(lines)


def _valid_product_lines(names):
    """The model's product lines, kept only if they are live workspaces, in
    the allow-list's spelling, de-duplicated, in the order given."""
    out = []
    for name in names or []:
        version_id = workspaces.id_for_name(name)
        if version_id and workspaces.LIVE_WORKSPACES[version_id] not in out:
            out.append(workspaces.LIVE_WORKSPACES[version_id])
    return out


def _pick_product_lines(tk, result):
    """(product_lines, source, basis) by the order in the module docstring:
    the ticket's field, else the lines the ticket names, else the model's
    prediction. ([], "", "") when there are none."""
    if tk.get("product_lines"):
        lines = _valid_product_lines(tk["product_lines"])
        if lines:
            return lines, "ticket", ""
    named = _valid_product_lines(result.get("product_lines"))
    if named:
        return named, "named", (result.get("product_lines_quote") or "").strip()
    predicted = _valid_product_lines(result.get("predicted_product_lines"))
    if predicted:
        return predicted, "predicted", (result.get("prediction_basis") or "").strip()
    return [], "", ""


def _predicted_comment(product_lines, basis):
    lines = ["The ticket doesn't say which product lines this change ships in, so I **predicted** them:", ""]
    lines += [f"- **{p}**" for p in product_lines]
    if basis:
        lines += ["", f"Why: {basis}"]
    lines += ["", "Please confirm them or say which to use instead before I search. Only these "
              "workspaces are searched."]
    return "\n".join(lines)


def _bounce(run, reasons):
    body = (
        "I can't start on this ticket yet:\n\n"
        + "\n".join(f"- {r}" for r in reasons)
        + "\n\nUpdate the ticket and move it to **In Draft** again. Set its product lines, or "
        "name them anywhere in the summary or description, for example "
        "\"This ships in DAP for Web and DAP for Desktop.\" The product lines are: "
        + ", ".join(workspaces.names()) + "."
    )
    ticket.record_comment(run, body, label="intake bounced")
    ticket.record_transition(run, ticket.TO_DO, actor="agent")


def run_intake(run):
    """Move the ticket To Do -> In Draft and extract its change note.
    Returns {"status": "ok", "change_note": path, ...} or
    {"status": "bounced", "reasons": [...]}."""
    rd = ticket.run_dir(run)
    tk = ticket.load_ticket(rd)
    if tk.get("status") != ticket.TO_DO:
        raise IntakeRefused(
            f"{tk['key']} is in {tk.get('status')!r}, not {ticket.TO_DO!r}: intake has already run. "
            f"Its change note is {rd / 'change_note.json'}."
        )
    ticket.record_transition(rd, ticket.IN_DRAFT, actor="writer")

    attachments, unread = [], []
    for path in ticket.attachment_paths(rd):
        a = pdf_text.read_attachment(path)
        (unread if a["problem"] else attachments).append(a)
    if unread:
        ticket.record_comment(rd, (
            "I couldn't read these attachments, so this run does not use them:\n\n"
            + "\n".join(f"- **{a['name']}** {a['problem']}." for a in unread)
            + "\n\nReplace them with text-based PDFs if they matter for this change."
        ), label="attachments not read")

    if not tk["summary"].strip() and not (tk.get("description") or "").strip() and not attachments:
        _bounce(rd, ["The ticket has no summary, description or readable attachment."])
        return {"status": "bounced", "reasons": ["no usable input"]}

    try:
        result = _extract(_system_prompt(), _request(tk, attachments))
    except Exception as exc:
        # Don't leave the ticket stranded in In Draft with no change note:
        # intake only runs from To Do, so it could never be retried.
        ticket.record_comment(rd, (
            "Something went wrong while I was reading this ticket, so I couldn't start on it:\n\n"
            f"`{type(exc).__name__}: {str(exc)[:300]}`\n\n"
            "Nothing was saved. Move the ticket to **In Draft** again to retry."
        ), label="intake failed")
        ticket.record_transition(rd, ticket.TO_DO, actor="agent")
        raise

    product_lines, source, basis = _pick_product_lines(tk, result)
    reasons = []
    if not product_lines:
        reasons.append("The ticket doesn't name a product line, and I couldn't predict one from it, "
                       "so I don't know which workspaces to search.")
    missing = [f for f in ("feature_area", "summary", "old", "new") if not (result.get(f) or "").strip()]
    if missing:
        reasons.append("I couldn't tell from the ticket what changed (no "
                       + ", ".join(missing) + ").")
    if reasons:
        _bounce(rd, reasons)
        return {"status": "bounced", "reasons": reasons, "extracted": result}

    note = ChangeNote(
        feature_area=result["feature_area"].strip(),
        summary=result["summary"].strip(),
        old=result["old"].strip(),
        new=result["new"].strip(),
        effective_date=(result.get("effective_date") or "").strip(),
        notes=(result.get("notes") or "").strip(),
        product_line=product_lines[0],  # read by discovery until it uses the list
        product_lines=product_lines,
        product_lines_source=source,
        product_lines_basis=basis,
        affected_content_types=list(result.get("affected_content_types") or []),
        unaffected_content_types=list(result.get("unaffected_content_types") or []),
        changes=[ContentChange(**c) for c in result.get("changes") or []],
        old_terms=_clean_terms(result.get("old_terms")),
    )
    suggested, suggest_error = [], None
    if not note.old_terms:
        try:
            suggested = _suggest_old_terms(_request(tk, attachments), result, product_lines)
        except Exception as exc:  # a suggestion is a nicety: never stop intake over it
            suggest_error = f"{type(exc).__name__}: {str(exc)[:200]}"
        note.old_terms_suggested = [s["term"] for s in suggested]
    path = save_change_note(note, str(rd / "change_note.json"))
    if source == "predicted":
        ticket.record_comment(rd, _predicted_comment(product_lines, basis), label="product lines predicted")
    ticket.record_comment(rd, _old_terms_comment(note.old_terms, suggested, suggest_error), label="old wording")
    ticket.record_event(rd, "intake", product_lines=product_lines, product_lines_source=source,
                        product_lines_basis=basis,
                        attachments_read=[a["name"] for a in attachments],
                        attachments_unread=[a["name"] for a in unread],
                        old_terms=note.old_terms, old_terms_suggested=suggested)
    return {"status": "ok", "change_note": path, "product_lines": product_lines,
            "product_lines_source": source, "product_lines_basis": basis,
            "old_terms": note.old_terms, "old_terms_suggested": suggested}


def main():
    parser = argparse.ArgumentParser(description="Extract a change note from a run's simulated Jira ticket.")
    parser.add_argument("run", help="Run name (under doc_sync/runs/) or path")
    args = parser.parse_args()
    try:
        outcome = run_intake(args.run)
    except IntakeRefused as exc:
        raise SystemExit(str(exc))
    if outcome["status"] == "bounced":
        print("Bounced to To Do:")
        for r in outcome["reasons"]:
            print(f"  - {r}")
        raise SystemExit(1)
    print(f"Change note: {outcome['change_note']}")
    print_product_lines(outcome)
    _print_old_terms(outcome)


SOURCE_LABELS = {
    "ticket": "set on the ticket",
    "named": "named in the ticket",
    "predicted": "PREDICTED, writer to confirm before phase 1",
}


def print_product_lines(outcome):
    label = SOURCE_LABELS.get(outcome.get("product_lines_source"), "")
    basis = outcome.get("product_lines_basis")
    print(f"Product lines: {', '.join(outcome['product_lines'])}"
          + (f"  ({label})" if label else "") + (f"\n  Basis: {basis}" if basis else ""))


def _print_old_terms(outcome):
    if outcome.get("old_terms"):
        print(f"Old terms (from the ticket): {', '.join(outcome['old_terms'])}")
    elif outcome.get("old_terms_suggested"):
        print("Old terms (SUGGESTED, writer to confirm): "
              + "; ".join(f"{s['term']} ({s['basis']})" for s in outcome["old_terms_suggested"]))
    else:
        print("Old terms: none stated or suggested")


if __name__ == "__main__":
    main()

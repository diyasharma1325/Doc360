"""Stage 1 (Intake): the structured note that drives both discovery
(candidates.py/kb_search.py) and assessment (assess.py/assess_gemini.py).
Everything downstream reads off this shape.

`old`/`new`/`summary` remain the required, always-present fields — a
one-line change is still valid as just those. The fields below them are
optional, additive structure for a change that touches several content
types at once (the common case once a change note comes from a ticket via
ticket_intake.py rather than being hand-typed):

  - `product_lines`: the live Document360 workspaces this change ships in
    (e.g. ["DAP for Web", "DAP for Desktop"]). Most changes span several,
    so it is a list. On a ticket run it is REQUIRED: ticket_intake.py
    extracts it from the ticket's description and stops the run if none
    is named. A note saved before this field existed loads its single
    `product_line` as a one-item list.
  - `product_line`: the single-workspace field `product_lines` replaces.
    Still read by discovery until it is switched to the list (intake
    fills it with the first product line meanwhile).
  - `affected_content_types` / `unaffected_content_types`: explicit lists
    instead of prose. This is what fixed the two real bugs discovery hit
    before this existed: keywords silently mined from exclusion language
    in `notes` ("Pop-ups did NOT move"), and `feature_area` itself never
    being used as a search term. An explicit list needs no NLP guessing,
    and unaffected_content_types lets discovery actively rule a category
    out rather than hoping no keyword happens to match it.
  - `changes`: a list of {content_type, old, new} for when different
    content types need different wording — one shared old/new sentence
    doesn't scale past two or three types without getting vague.
  - `old_terms` / `old_terms_suggested` (2026-11-09): the UI wording the
    OUTDATED articles use for the old state ("Widgets tab"), which is what
    discovery has to search for: a stale article doesn't contain the new
    wording yet. `old_terms` is what the ticket or an attachment stated;
    `old_terms_suggested` is intake's suggestion when it stated none, from
    the product reference, shown to the writer to confirm. Discovery uses
    both. A Launchers ticket that never said "Widgets" searched only for
    "Content tab" and missed the articles still saying "Widgets".

A change note with only the required fields still works everywhere;
code that wants the richer structure checks whether these are populated
and falls back to old/new/summary when they're not.
"""
import argparse
import json
import os
from dataclasses import asdict, dataclass, field
from typing import List


@dataclass
class ContentChange:
    content_type: str   # e.g. "Smart Tips", "Beacons", "Flows"
    old: str
    new: str


@dataclass
class ChangeNote:
    feature_area: str    # must match a key you seed into data/tag_map.json
    summary: str          # one line: what changed
    old: str              # the label, behavior, or UI text being replaced
    new: str              # what it becomes
    effective_date: str = ""  # ISO date the change goes/went live — optional, informational only
    notes: str = ""       # anything else worth telling the agent
    product_line: str = ""  # real Document360 workspace name, e.g. "DAP for Web"
    product_lines: List[str] = field(default_factory=list)  # every live workspace the change ships in
    affected_content_types: List[str] = field(default_factory=list)
    unaffected_content_types: List[str] = field(default_factory=list)
    changes: List[ContentChange] = field(default_factory=list)
    old_terms: List[str] = field(default_factory=list)
    old_terms_suggested: List[str] = field(default_factory=list)

    def all_old_terms(self):
        """Stated old terms, then suggested ones, de-duplicated."""
        out = []
        for t in list(self.old_terms or []) + list(self.old_terms_suggested or []):
            if t and t.strip() and t.strip().lower() not in [o.lower() for o in out]:
                out.append(t.strip())
        return out


REQUIRED_FIELDS = ["feature_area", "summary", "old", "new"]
# effective_date is optional and informational: nothing in discovery or
# assessment depends on it. ticket_intake.py records it when the ticket or
# an attachment states one.


def load_change_note(path):
    with open(path) as f:
        data = json.load(f)
    missing = [k for k in REQUIRED_FIELDS if not data.get(k)]
    if missing:
        raise ValueError(f"{path} is missing required field(s): {', '.join(missing)}")
    product_line = data.get("product_line", "")
    product_lines = list(data.get("product_lines") or ([product_line] if product_line else []))
    return ChangeNote(
        feature_area=data["feature_area"],
        summary=data["summary"],
        old=data["old"],
        new=data["new"],
        effective_date=data.get("effective_date", ""),
        notes=data.get("notes", ""),
        product_line=product_line,
        product_lines=product_lines,
        affected_content_types=list(data.get("affected_content_types") or []),
        unaffected_content_types=list(data.get("unaffected_content_types") or []),
        changes=[ContentChange(**c) for c in data.get("changes") or []],
        old_terms=list(data.get("old_terms") or []),
        old_terms_suggested=list(data.get("old_terms_suggested") or []),
    )


def save_change_note(note, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(asdict(note), f, indent=2)
    return path


def scaffold(path):
    if os.path.exists(path):
        raise FileExistsError(f"{path} already exists — not overwriting")
    template = {
        "feature_area": "",
        "summary": "",
        "old": "",
        "new": "",
        "effective_date": "",
        "notes": "",
        "product_line": "",
        "product_lines": [],
        "affected_content_types": [],
        "unaffected_content_types": [],
        "changes": [],
        "old_terms": [],
        "old_terms_suggested": [],
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(template, f, indent=2)
    return path


def main():
    parser = argparse.ArgumentParser(description="Scaffold or validate a change note.")
    sub = parser.add_subparsers(dest="command", required=True)

    new_p = sub.add_parser("new", help="Write a blank change note template")
    new_p.add_argument("--out", required=True, help="Path to write, e.g. data/changes/my_change.json")

    check_p = sub.add_parser("check", help="Validate an existing change note")
    check_p.add_argument("path")

    args = parser.parse_args()
    if args.command == "new":
        path = scaffold(args.out)
        print(f"Wrote template to {path} — fill it in before running the pipeline.")
    else:
        note = load_change_note(args.path)
        print(json.dumps(asdict(note), indent=2))
        print("\nLooks valid.")


if __name__ == "__main__":
    main()

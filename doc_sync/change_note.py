"""Stage 1 (Intake): the structured note that drives both discovery
(candidates.py/kb_search.py) and assessment (assess.py/assess_gemini.py).
Everything downstream reads off this shape.

`old`/`new`/`summary` remain the required, always-present fields — a
one-line change is still valid as just those. The fields below them are
optional, additive structure for a change that touches several content
types at once (the common case once a change note comes from a PRD via
prd_intake.py rather than being hand-typed):

  - `product_line`: the real Document360 workspace this applies to (e.g.
    "DAP for Web"), read directly by kb_search.py instead of requiring a
    --product-line flag or a human remembering to set one.
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
    effective_date: str   # ISO date the change goes/went live
    notes: str = ""       # anything else worth telling the agent
    product_line: str = ""  # real Document360 workspace name, e.g. "DAP for Web"
    affected_content_types: List[str] = field(default_factory=list)
    unaffected_content_types: List[str] = field(default_factory=list)
    changes: List[ContentChange] = field(default_factory=list)


REQUIRED_FIELDS = ["feature_area", "summary", "old", "new"]
# effective_date is deliberately NOT required at load time: prd_intake.py
# leaves it blank rather than guess when a PRD doesn't state one, and a
# blank date doesn't actually affect discovery or assessment correctness
# today — it's informational. A human still ought to review and fill it
# in; webapp.py's PRD flow has a review step for exactly that, it's just
# not enforced by this loader.


def load_change_note(path):
    with open(path) as f:
        data = json.load(f)
    missing = [k for k in REQUIRED_FIELDS if not data.get(k)]
    if missing:
        raise ValueError(f"{path} is missing required field(s): {', '.join(missing)}")
    return ChangeNote(
        feature_area=data["feature_area"],
        summary=data["summary"],
        old=data["old"],
        new=data["new"],
        effective_date=data["effective_date"],
        notes=data.get("notes", ""),
        product_line=data.get("product_line", ""),
        affected_content_types=list(data.get("affected_content_types") or []),
        unaffected_content_types=list(data.get("unaffected_content_types") or []),
        changes=[ContentChange(**c) for c in data.get("changes") or []],
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
        "affected_content_types": [],
        "unaffected_content_types": [],
        "changes": [],
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

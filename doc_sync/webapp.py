"""Local web interface for the doc-sync pipeline — the non-engineer-
facing input/output surface requested to sit alongside the CLI, not
replace it. Wraps the exact same functions the CLI uses (change_note,
pipeline.run, review_queue) — no separate logic, no separate data.

Run with:
    python3 doc_sync/webapp.py
then open http://127.0.0.1:5000 in a browser.
"""
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

import pipeline
import review_queue
import tag_map
import workspaces
from change_note import ChangeNote, save_change_note

app = Flask(__name__)

CHANGES_DIR = Path(__file__).parent / "data" / "changes"

DISCOVERY_MODES = ("titles", "index")  # same choices as pipeline.py run --discovery


def _discovery_mode(values):
    """The discovery mode a form or query string asked for; anything
    unrecognized means "titles", the pipeline's default."""
    mode = values.get("discovery", "titles")
    return mode if mode in DISCOVERY_MODES else "titles"


def _lines(text):
    """A one-per-line textarea -> its non-blank lines, trimmed."""
    return [line.strip() for line in text.splitlines() if line.strip()]


def _index_status():
    """kb_index.status(), for the discovery-mode picker to show whether
    "index" mode will actually run or fall back to titles."""
    import kb_index

    return kb_index.status()


@app.route("/")
def home():
    return redirect(url_for("queue_view"))


@app.route("/new", methods=["GET", "POST"])
def new_change():
    if request.method == "POST":
        note = ChangeNote(
            feature_area=request.form["feature_area"].strip(),
            summary=request.form["summary"].strip(),
            old=request.form["old"].strip(),
            new=request.form["new"].strip(),
            notes=request.form.get("notes", "").strip(),
            product_line=request.form.get("product_line", "").strip(),
            affected_content_types=_lines(request.form.get("affected_content_types", "")),
            unaffected_content_types=_lines(request.form.get("unaffected_content_types", "")),
        )
        path = CHANGES_DIR / f"{note.feature_area}.json"
        save_change_note(note, path)
        discovery = _discovery_mode(request.form)
        # Always goes through /discover now, not straight to /run — a
        # feature_area that doesn't exactly match a tag_map entry used to
        # hard-fail here (LookupError, 2026-10-29); now it falls through to
        # a live KB search instead, and that can mean spending one model
        # call and finding many candidates, so it still needs a human to
        # pick a deliberate subset before assessment runs, same as a
        # PRD-derived note.
        return redirect(url_for("discover_candidates", path=str(path), discovery=discovery))

    feature_areas = sorted(tag_map.load().keys())
    return render_template(
        "new_change.html", feature_areas=feature_areas, index_status=_index_status(),
        product_lines=workspaces.names(),
    )


@app.route("/new/prd", methods=["POST"])
def new_change_from_prd():
    # Same end point as the manual form below (a saved ChangeNote), but
    # produced by one model call reading a PRD instead of a person
    # filling in five fields by hand. See prd_intake.py for what it does
    # and does not infer, and why effective_date/product_line are left
    # blank rather than guessed when the PRD doesn't clearly state them.
    # A PDF upload wins over pasted text when both are given — it's read
    # natively (tables, embedded images included), not flattened to text.
    import prd_intake

    uploaded = request.files.get("prd_file")
    if uploaded and uploaded.filename.lower().endswith(".pdf"):
        note = prd_intake.extract_change_note(uploaded.read(), is_pdf=True)
    else:
        prd_text = request.form.get("prd_text", "").strip()
        if not prd_text:
            return redirect(url_for("new_change"))
        note = prd_intake.extract_change_note(prd_text)

    path = CHANGES_DIR / f"{note.feature_area}.json"
    save_change_note(note, path)
    # Extraction deliberately leaves fields blank rather than guessing —
    # review_extracted.html is where a human actually gets to see and
    # fill those in before anything downstream runs on them.
    return redirect(url_for("review_extracted", path=str(path)))


@app.route("/new/review", methods=["GET", "POST"])
def review_extracted():
    import json as json_module

    path = request.values["path"]

    if request.method == "POST":
        note = ChangeNote(
            feature_area=request.form["feature_area"].strip(),
            summary=request.form["summary"].strip(),
            old=request.form["old"].strip(),
            new=request.form["new"].strip(),
            effective_date=request.form.get("effective_date", "").strip(),
            notes=request.form.get("notes", "").strip(),
            product_line=request.form.get("product_line", "").strip(),
            affected_content_types=_lines(request.form.get("affected_content_types", "")),
            unaffected_content_types=_lines(request.form.get("unaffected_content_types", "")),
        )
        save_change_note(note, path)
        # A PRD-derived note has no tag_map entry to look candidates up
        # from — it goes straight to live KB discovery instead of the
        # tag_map path the manual form uses.
        return redirect(url_for("discover_candidates", path=path, discovery=_discovery_mode(request.form)))

    # Raw JSON, not load_change_note() — this screen's entire purpose is
    # letting a human see and fill in exactly the blanks load_change_note
    # would otherwise accept silently.
    with open(path) as f:
        note = json_module.load(f)
    note.setdefault("affected_content_types", [])
    note.setdefault("unaffected_content_types", [])
    return render_template("review_extracted.html", path=path, note=note, index_status=_index_status())


@app.route("/discover")
def discover_candidates():
    # The candidate-selection step between discovery and assessment. First
    # checks tag_map.json — free, instant, for a feature area that's
    # already hand-seeded — before ever falling through to a live KB
    # search (keyword floor, free, plus one model call for the semantic
    # pass). Either way, the human picks which candidates are actually
    # worth spending an assessment call on — that's the part that costs
    # one model call *per article*, so showing the list before committing
    # to that matters regardless of which source found them.
    import candidates
    import mock_d360
    from change_note import load_change_note

    path = request.args["path"]
    note = load_change_note(path)

    cached_ids = candidates.find_candidates(note)
    if cached_ids:
        mock_client = mock_d360.MockDocument360Client()
        found = [
            {
                "article_id": article_id,
                "title": mock_client.get_article(article_id)["data"].get("title", article_id),
                "reason": "hand-seeded tag_map entry — no live search needed",
            }
            for article_id in cached_ids
        ]
        return render_template(
            "discover.html", path=path, source="tag_map",
            scanned_count=len(cached_ids), found=found,
        )

    import kb_search

    # "index" searches every live workspace (see kb_search.py); the note's
    # product_line only scopes "titles" mode, same as pipeline.py run.
    # Falls back to "titles" when no index is built, and the page says so.
    discovery = _discovery_mode(request.args)
    indexed = discovery == "index" and kb_search.index_available()
    # The note's product lines scope both modes (kb_search.resolve_scope);
    # every candidate record carries its workspace.
    scope = kb_search.resolve_scope(note, None, "index" if indexed else "titles")
    _, found, scanned = kb_search.find_candidates_live(note, discovery=discovery)
    return render_template(
        "discover.html", path=path, source="kb", product_line=", ".join(scope),
        scanned_count=len(scanned), found=found,
        discovery=discovery, indexed=indexed, index_status=_index_status(),
    )


@app.route("/run", methods=["POST"])
def run_change():
    # Only ever reached from /discover's confirm form now — a human has
    # already picked which discovered candidates (tag_map or live KB) are
    # worth spending an assessment call on.
    path = request.form["path"]
    only_ids = request.form.getlist("article_id") or None

    try:
        # Explicit ids skip discovery, so no scope is needed here.
        results = pipeline.run(path, only_ids=only_ids)
        error = None
    except Exception as exc:
        results, error = None, str(exc)
    return render_template("run_result.html", error=error, results=results)


@app.route("/queue")
def queue_view():
    return render_template("queue.html", items=review_queue.list_pending())


@app.route("/queue/<item_id>/<action>", methods=["POST"])
def resolve_item(item_id, action):
    status = "approved" if action == "approve" else "rejected"
    review_queue.mark(item_id, status)
    return redirect(url_for("queue_view"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)

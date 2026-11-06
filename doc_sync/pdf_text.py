"""PDF attachment -> plain text for ticket intake.

`claude -p` takes text, not files, so a ticket's PDF attachments (PRDs,
product notes) are read here first. Adapted from the I2P agent's
extractor/prd_parser.py: pdfplumber, with each table rendered inline as
Markdown, because a flat text extract interleaves adjacent columns and a
field spec or permission matrix would reach the model as an ambiguous run
of words.

Limits are the I2P agent's (jira/config.py): 10 MB and 300 pages per PDF.
A PDF over either, not a real PDF, or with no extractable text (a scanned
export) is NOT read and NOT fatal: read_attachment() reports why, and
ticket intake records it on the ticket instead of silently planning
without it (the I2P agent's known gap).

    python3 doc_sync/pdf_text.py <file.pdf>      # print what intake would see
"""
import argparse
from pathlib import Path

import pdfplumber

MAX_BYTES = 10_000_000
MAX_PAGES = 300


def _clean_cell(cell):
    if cell is None:
        return ""
    return " ".join(str(cell).split()).replace("|", "\\|")


def _table_to_markdown(table):
    try:
        rows = table.extract()
    except Exception:
        return ""
    cleaned = []
    for row in rows or []:
        cells = [_clean_cell(c) for c in row]
        if any(cells):
            cleaned.append(cells)
    if not cleaned:
        return ""
    ncols = max(len(r) for r in cleaned)
    cleaned = [r + [""] * (ncols - len(r)) for r in cleaned]
    header, body = cleaned[0], cleaned[1:]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * ncols) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(lines)


def _crop_text(page, x0, top, x1, bottom):
    if bottom - top <= 1:
        return ""
    try:
        return (page.crop((x0, top, x1, bottom)).extract_text() or "").strip()
    except Exception:
        return ""


def _page_with_tables(page, tables):
    """Prose bands between tables, each table as Markdown, top to bottom.
    PRDs are single-column, so a full-width band never duplicates cell text."""
    px0, ptop, px1, pbottom = page.bbox
    parts, cursor = [], ptop
    for table in sorted(tables, key=lambda t: t.bbox[1]):
        _, t_top, _, t_bottom = table.bbox
        band = _crop_text(page, px0, cursor, px1, t_top)
        if band:
            parts.append(band)
        md = _table_to_markdown(table)
        if md:
            parts.append(md)
        cursor = max(cursor, t_bottom)
    trailing = _crop_text(page, px0, cursor, px1, pbottom)
    if trailing:
        parts.append(trailing)
    return "\n\n".join(parts).strip()


def _page_text(page):
    """Falls back to a flat extract on any table failure, so a table quirk
    never loses the page's prose."""
    try:
        tables = page.find_tables()
    except Exception:
        tables = []
    if not tables:
        return (page.extract_text() or "").strip()
    try:
        return _page_with_tables(page, tables) or (page.extract_text() or "").strip()
    except Exception:
        return (page.extract_text() or "").strip()


def read_attachment(path):
    """-> {"name", "pages", "text", "problem"}. Exactly one of `text` and
    `problem` is non-empty. Never raises for a bad file."""
    path = Path(path)
    out = {"name": path.name, "pages": 0, "text": "", "problem": ""}
    try:
        size = path.stat().st_size
    except OSError as exc:
        out["problem"] = f"could not be opened ({exc.strerror or exc})"
        return out
    if size > MAX_BYTES:
        out["problem"] = f"is {size / 1_000_000:.1f} MB, over the {MAX_BYTES // 1_000_000} MB limit"
        return out
    try:
        with pdfplumber.open(path) as pdf:
            out["pages"] = len(pdf.pages)
            if out["pages"] > MAX_PAGES:
                out["problem"] = f"has {out['pages']} pages, over the {MAX_PAGES}-page limit"
                return out
            texts = [t for t in (_page_text(p) for p in pdf.pages) if t]
    except Exception as exc:
        out["problem"] = f"is not a readable PDF ({type(exc).__name__})"
        return out
    if not texts:
        out["problem"] = "has no extractable text (it may be a scanned image)"
        return out
    out["text"] = "\n\n".join(texts)
    return out


def main():
    parser = argparse.ArgumentParser(description="Print the text ticket intake would read from a PDF.")
    parser.add_argument("pdf")
    args = parser.parse_args()
    result = read_attachment(args.pdf)
    if result["problem"]:
        raise SystemExit(f"{result['name']} {result['problem']}")
    print(f"--- {result['name']}: {result['pages']} page(s), {len(result['text']):,} characters ---")
    print(result["text"])


if __name__ == "__main__":
    main()

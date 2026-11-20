"""Screenshots: everything Doc Sync does with an article's images, apart
from judging them (image_review.py).

- READ: the images in an article's HTML, each with its position, path,
  alt text and the step text before it (article_images).
- FETCH + PREPARE: download one, save it as a PNG a vision call can Read.
  An animated GIF becomes ONE image tiling 4 sampled frames, because a
  call given several frame files skipped the later ones (feasibility
  check, 2026-11-19).
- OCR: Tesseract, plain (psm 3) on the first frame. Upscaled + greyscale
  read worse (2 of 7 old labels against 7 of 7), so there is no
  preprocessing.
- SWAP: change one image's src (and alt) in the HTML, and nothing else, so
  each tag keeps its own width and settings.
- THE SCREENSHOT RECORD (data/screenshots.db, git-ignored, kept across
  index rebuilds): OCR text per image path, every verdict a review gave,
  and which images are known to show a change's NEW UI, which is what
  replacement suggestions draw on.

Image URLs: Document360 serves every image with a time-limited signature
(?sv=...&sig=...) and re-signs it on every read; the bare path 404s. So an
image is identified by its path WITHOUT the query string, a download must
use a src from a fresh read, and a src written into an article may be the
bare path (Document360 signs it on the next read; checked 2026-11-20 on a
draft written 9 days earlier).

    python3 doc_sync/screenshots.py ocr [--workspace "DAP for Web"]   # fill OCR in place
    python3 doc_sync/screenshots.py status
"""
import argparse
import hashlib
import html as html_lib
import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR.parent / "core"))

DB_PATH = os.environ.get("SCREENSHOTS_DB_PATH") or str(THIS_DIR / "data" / "screenshots.db")

MAX_SIDE = 1600        # a still image sent to vision is shrunk to fit this
TILE_SIDE = 800        # each GIF frame in the 2x2 tile
STEP_TEXT_CHARS = 300  # the step text kept with each image

# Upload limits, the same as the I2P agent's /push-screenshots (screenshot/routes.py).
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_UPLOAD_PIXELS = 40_000_000

_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_SRC_ATTR_RE = re.compile(r'(\ssrc\s*=\s*)(["\'])(.*?)\2', re.IGNORECASE | re.DOTALL)
_ALT_ATTR_RE = re.compile(r'(\salt\s*=\s*)(["\'])(.*?)\2', re.IGNORECASE | re.DOTALL)


# --- reading images out of HTML -------------------------------------------------

def image_path(src):
    """An image URL without its query string or fragment, unescaped: the
    stable name of an image (the signature changes on every read)."""
    return html_lib.unescape(src or "").split("#", 1)[0].split("?", 1)[0]


def _step_text(img):
    """The nearest preceding text of some length: the step the screenshot
    illustrates."""
    for prev in img.find_all_previous(string=True, limit=40):
        t = " ".join(prev.split())
        if len(t) > 25:
            return t[:STEP_TEXT_CHARS]
    return ""


def article_images(html_content):
    """[{n, src, path, alt, step_text}] for every <img> in the HTML, in
    order; n is 1-based (the writer-facing "image 3"). An image that
    appears twice is listed twice, with the same path."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content or "", "html.parser")
    out = []
    for n, img in enumerate(soup.find_all("img"), 1):
        src = img.get("src") or ""
        out.append({"n": n, "src": html_lib.unescape(src), "path": image_path(src),
                    "alt": img.get("alt") or "", "step_text": _step_text(img)})
    return out


def swap_src(html_content, old_path, new_src, new_alt=None):
    """`html_content` with every <img> whose path is `old_path` pointing at
    `new_src` instead (and given `new_alt`, when one is passed). Edits only
    those attributes, as text, so the rest of the article, and the rest of
    each tag, is left byte for byte. Returns (html, number of tags changed)."""
    changed = 0
    src_attr = html_lib.escape(new_src, quote=True)
    alt_attr = html_lib.escape(new_alt, quote=True) if new_alt is not None else None

    def one(match):
        nonlocal changed
        tag = match.group(0)
        m = _SRC_ATTR_RE.search(tag)
        if not m or image_path(m.group(3)) != old_path:
            return tag
        changed += 1
        tag = tag[:m.start()] + f'{m.group(1)}"{src_attr}"' + tag[m.end():]
        if alt_attr is not None:
            a = _ALT_ATTR_RE.search(tag)
            if a:
                tag = tag[:a.start()] + f'{a.group(1)}"{alt_attr}"' + tag[a.end():]
            else:
                tag = re.sub(r"^<img\b", f'<img alt="{alt_attr}"', tag, count=1, flags=re.IGNORECASE)
        return tag

    return _IMG_TAG_RE.sub(one, html_content or ""), changed


# --- fetching and preparing -----------------------------------------------------

FETCH_DEADLINE_S = 45          # a whole download, not one read
FETCH_MAX_BYTES = 30 * 1024 * 1024


def fetch(src, attempts=3):
    """The image's bytes. `src` must be a freshly read, signed URL. Each try
    has an OVERALL deadline: requests' timeout applies per read, so a
    download that trickles in would never trip it."""
    import requests

    for attempt in range(1, attempts + 1):
        try:
            started, chunks, size = time.time(), [], 0
            with requests.get(html_lib.unescape(src), timeout=(10, 15), stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(65536):
                    chunks.append(chunk)
                    size += len(chunk)
                    if size > FETCH_MAX_BYTES:
                        raise ValueError(f"image over {FETCH_MAX_BYTES // 1_048_576} MB")
                    if time.time() - started > FETCH_DEADLINE_S:
                        raise TimeoutError(f"download took over {FETCH_DEADLINE_S}s")
            return b"".join(chunks)
        except ValueError:
            raise
        except Exception:
            if attempt == attempts:
                raise
            time.sleep(2 * attempt)


def _open(data):
    from PIL import Image

    return Image.open(io.BytesIO(data))


def frame_count(data):
    return getattr(_open(data), "n_frames", 1)


def prepare(data, out_dir, name):
    """Save the image as `<name>.png` in `out_dir`, ready for a vision call to
    Read: a still image shrunk to fit MAX_SIDE, or for an animated GIF one
    2x2 sheet of 4 sampled frames in reading order. Returns (file name,
    frame count)."""
    from PIL import Image

    im = _open(data)
    n = getattr(im, "n_frames", 1)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if n == 1:
        frame = im.convert("RGB")
        if max(frame.size) > MAX_SIDE:
            frame.thumbnail((MAX_SIDE, MAX_SIDE))
        frame.save(out_dir / f"{name}.png")
        return f"{name}.png", 1
    tiles = []
    for k in sorted({0, n // 3, (2 * n) // 3, n - 1}):
        im.seek(k)
        f = im.convert("RGB")
        f.thumbnail((TILE_SIDE, TILE_SIDE))
        tiles.append(f)
    w, h = max(t.width for t in tiles), max(t.height for t in tiles)
    sheet = Image.new("RGB", (w * 2, h * ((len(tiles) + 1) // 2)), "white")
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 2) * w, (i // 2) * h))
    sheet.save(out_dir / f"{name}.png")
    return f"{name}.png", n


def check_upload(data):
    """Why these bytes can't be uploaded as a screenshot, or "" if they can:
    PNG only, at most 10 MB and 40 megapixels (the I2P agent's limits)."""
    if not data:
        return "the file is empty"
    if len(data) > MAX_UPLOAD_BYTES:
        return f"it is {len(data) / 1_048_576:.1f} MB; the limit is 10 MB"
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "it is not a PNG (save it as .png)"
    try:
        im = _open(data)
        w, h = im.size
    except Exception as exc:
        return f"it could not be read as an image ({type(exc).__name__})"
    if w * h > MAX_UPLOAD_PIXELS:
        return f"it is {w}x{h}, over the 40-megapixel limit"
    return ""


# --- OCR ------------------------------------------------------------------------

def tesseract_available():
    return shutil.which("tesseract") is not None


def ocr(data):
    """The text Tesseract reads in the image (first frame), on one line."""
    from PIL import Image  # noqa: F401  (Pillow must be present to decode)

    im = _open(data).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "PNG")
    r = subprocess.run(["tesseract", "stdin", "stdout", "--psm", "3"], input=buf.getvalue(),
                       capture_output=True, timeout=120)
    return " ".join(r.stdout.decode("utf-8", "replace").split())


def sha1(data):
    return hashlib.sha1(data).hexdigest()


# --- the screenshot record ------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ocr (
    path TEXT PRIMARY KEY, sha1 TEXT, width INTEGER, height INTEGER, frames INTEGER,
    text TEXT NOT NULL, at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS verdicts (
    path TEXT NOT NULL, feature_area TEXT NOT NULL, article_id TEXT, image_n INTEGER,
    verdict TEXT NOT NULL, what_is_visible TEXT, reason TEXT, run TEXT, at TEXT NOT NULL,
    PRIMARY KEY (path, feature_area)
);
CREATE TABLE IF NOT EXISTS current (
    path TEXT NOT NULL, feature_area TEXT NOT NULL, src TEXT NOT NULL, source TEXT NOT NULL,
    article_id TEXT, title TEXT, image_n INTEGER, description TEXT, run TEXT, at TEXT NOT NULL,
    PRIMARY KEY (path, feature_area)
);
"""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path=None):
    db_path = db_path or DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # readers never wait on a writer; OCR threads write concurrently
    conn.executescript(_SCHEMA)
    return conn


def cached_ocr(paths, db_path=None):
    """{path: text} for the paths whose OCR is already recorded."""
    paths = list(dict.fromkeys(p for p in paths if p))
    if not paths or not os.path.exists(db_path or DB_PATH):
        return {}
    conn = connect(db_path)
    try:
        out = {}
        for i in range(0, len(paths), 500):
            chunk = paths[i:i + 500]
            rows = conn.execute(f"SELECT path, text FROM ocr WHERE path IN ({','.join('?' * len(chunk))})", chunk)
            out.update({r["path"]: r["text"] for r in rows})
        return out
    finally:
        conn.close()


def record_ocr(path, data, text, conn):
    try:
        im = _open(data)
        w, h, frames = im.size[0], im.size[1], getattr(im, "n_frames", 1)
    except Exception:
        w = h = frames = None
    conn.execute("INSERT OR REPLACE INTO ocr VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (path, sha1(data), w, h, frames, text, _now()))


def ocr_images(images, db_path=None, workers=4, log=print):
    """OCR every image in `images` ([{path, src}], srcs freshly signed)
    whose path isn't recorded yet. Returns {path: text} for all of them
    (cached and new). A download or OCR failure is skipped and logged, never
    raised: OCR only helps discovery, it must never stop a build."""
    from concurrent.futures import ThreadPoolExecutor

    by_path = {}
    for im in images:
        if im.get("path") and im["path"] not in by_path:
            by_path[im["path"]] = im["src"]
    have = cached_ocr(by_path, db_path)
    todo = [(p, s) for p, s in by_path.items() if p not in have]
    if not todo or not tesseract_available():
        return have

    def work(item):
        path, src = item
        try:
            data = fetch(src)
            return path, data, ocr(data)
        except Exception as exc:
            return path, None, f"{type(exc).__name__}: {exc}"

    # Download and read first, then write in one short transaction: holding a
    # write open through the downloads locked out the other OCR threads of a
    # build ("database is locked", 2026-11-20).
    with ThreadPoolExecutor(max_workers=workers) as pool:
        done = list(pool.map(work, todo))
    failed = sum(1 for _, data, _ in done if data is None)
    conn = connect(db_path)
    try:
        for path, data, text in done:
            if data is not None:
                record_ocr(path, data, text, conn)
                have[path] = text
        conn.commit()
    finally:
        conn.close()
    if failed:
        log(f"    (OCR skipped {failed} image(s) that could not be downloaded or read)")
    return have


def screens_text(images, ocr_by_path):
    """The OCR text of an article's images as indexable lines:
    "Screenshot 3: <text>". Images with no text are left out."""
    lines, seen = [], set()
    for im in images:
        text = (ocr_by_path.get(im["path"]) or "").strip()
        if text and im["path"] not in seen:
            seen.add(im["path"])
            lines.append(f"Screenshot {im['n']}: {text}")
    return "\n".join(lines)


def record_verdicts(feature_area, article_id, items, run=None, db_path=None):
    """Save a review's verdicts ([{path, n, verdict, what_is_visible,
    reason}]) for this change, replacing earlier ones for the same image."""
    conn = connect(db_path)
    try:
        conn.executemany("INSERT OR REPLACE INTO verdicts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            (i["path"], feature_area, article_id, i.get("n"), i["verdict"], i.get("what_is_visible", ""),
             i.get("reason", ""), run, _now()) for i in items if i.get("path")])
        conn.commit()
    finally:
        conn.close()


def record_current(feature_area, path, src, source, article_id="", title="", image_n=None, description="",
                   run=None, db_path=None):
    """Mark an image as showing this change's NEW UI. `source`: "uploaded"
    (a writer's retake, checked), "reused" (a suggestion the writer kept) or
    "reviewed" (judged fine and showing the changed area)."""
    conn = connect(db_path)
    try:
        conn.execute("INSERT OR REPLACE INTO current VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     (path, feature_area, src, source, article_id, title, image_n, description, run, _now()))
        conn.commit()
    finally:
        conn.close()


def forget_current(feature_area, path, db_path=None):
    conn = connect(db_path)
    try:
        conn.execute("DELETE FROM current WHERE path = ? AND feature_area = ?", (path, feature_area))
        conn.commit()
    finally:
        conn.close()


def current_images(feature_area, db_path=None):
    """[{path, src, source, article_id, title, image_n, description}] known
    to show this change's new UI."""
    if not os.path.exists(db_path or DB_PATH):
        return []
    conn = connect(db_path)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM current WHERE feature_area = ?", (feature_area,))]
    finally:
        conn.close()


def status(db_path=None):
    if not os.path.exists(db_path or DB_PATH):
        return {"exists": False}
    conn = connect(db_path)
    try:
        q = lambda sql: conn.execute(sql).fetchone()[0]
        return {"exists": True, "ocr_images": q("SELECT count(*) FROM ocr"),
                "ocr_with_text": q("SELECT count(*) FROM ocr WHERE text != ''"),
                "verdicts": q("SELECT count(*) FROM verdicts"),
                "current_images": q("SELECT count(*) FROM current"),
                "changes": [r[0] for r in conn.execute("SELECT DISTINCT feature_area FROM current")]}
    finally:
        conn.close()


# --- CLI: fill OCR for one workspace, in place -----------------------------------

def ocr_workspace(workspace=None, db_path=None):
    """Read every indexed article (in one workspace, or all), OCR its images
    not recorded yet, and write the result into the knowledge index in place
    (kb_index.update_screens). Read-only against Document360."""
    import kb_index
    from d360_client import Document360Client

    ids = kb_index.article_ids(workspace=workspace)
    client = Document360Client()
    print(f"OCR for {len(ids)} article(s){' in ' + workspace if workspace else ''}...", flush=True)
    updates = {}
    for k, aid in enumerate(ids, 1):
        try:
            data = kb_index._fetch_article(client, aid)
        except Exception as exc:
            print(f"    skipped {aid}: {exc}")
            continue
        images = article_images(data.get("html_content") or "")
        if images:
            ocr_by_path = ocr_images(images, db_path)
            updates[aid] = (images, screens_text(images, ocr_by_path))
        if k % 50 == 0:
            print(f"    {k}/{len(ids)}", flush=True)
        time.sleep(kb_index.REQUEST_GAP_S)
    n = kb_index.update_screens(updates)
    print(f"Updated the screenshot text of {n} article(s) in the knowledge index.")


def main():
    p = argparse.ArgumentParser(description="Doc Sync's screenshot record and OCR.")
    sub = p.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("ocr", help="OCR the images of indexed articles and update the index in place")
    o.add_argument("--workspace", default=None)
    sub.add_parser("status")
    args = p.parse_args()
    if args.cmd == "ocr":
        if not tesseract_available():
            raise SystemExit("Tesseract is not installed (brew install tesseract).")
        try:
            from dotenv import load_dotenv
            load_dotenv(THIS_DIR.parent / ".env")
        except ImportError:
            pass
        ocr_workspace(args.workspace)
    else:
        print(json.dumps(status(), indent=2))


if __name__ == "__main__":
    main()

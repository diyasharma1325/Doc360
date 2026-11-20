"""Upload a screenshot to Document360 Drive and get the URL to put in an
article. Adapted from the I2P agent's screenshot/doc360_drive.py, which
worked out the contract of this undocumented endpoint:

- POST /v2/Drive/Folders/Files, one multipart part named `files` (plural).
- DriveFolderId and UserId go in the QUERY STRING; Document360 rejects them
  as form fields ("field is required").
- Prefer the URL the response returns: Drive renames a file on a name
  collision. A response without one falls back to the public path
  (files.document360.io/<project>/Images/Documentation/<name>), flagged as
  unverified.

Settings (.env): D360_API_KEY, D360_DRIVE_FOLDER_ID (the Drive folder the
I2P agent uploads into; writer decision 2026-11-20: Doc Sync uses the same
one), D360_USER_ID (the writer's Document360 user id) and
D360_DRIVE_PROJECT_ID (the project id in image URLs, for the fallback URL).
NOT D360_FOLDER_ID: in this repo that is a category id (core/articles.py),
and Drive rejects it ("Invalid FolderId / ProjectId", 2026-11-20).

The only Document360 write Doc Sync makes outside the Archived scratch
articles. A Drive upload adds a file; it never changes an article, and
nothing here deletes anything.
"""
import os

import requests

DRIVE_UPLOAD_URL = "https://apihub.document360.io/v2/Drive/Folders/Files"
PUBLIC_FILES_BASE = "https://files.document360.io"


class DriveUploadError(RuntimeError):
    pass


def _setting(name):
    value = (os.environ.get(name) or "").strip()
    if not value:
        raise DriveUploadError(f"{name} is not set in .env; it is needed to upload screenshots to Document360 Drive.")
    return value


def configured():
    """'' when every setting is present, else what is missing."""
    missing = [n for n in ("D360_API_KEY", "D360_DRIVE_FOLDER_ID", "D360_DRIVE_PROJECT_ID", "D360_USER_ID")
               if not (os.environ.get(n) or "").strip()]
    return ", ".join(missing)


def upload_png(filename, png_bytes, post=requests.post):
    """Upload one PNG; returns (url, verified). `verified` is False when the
    response gave no URL and the public path was built instead. Raises
    DriveUploadError. `post` is for tests."""
    if not filename.lower().endswith(".png"):
        raise DriveUploadError(f"filename must end in .png (got {filename!r})")
    if not png_bytes:
        raise DriveUploadError("the image is empty")
    try:
        r = post(DRIVE_UPLOAD_URL, headers={"api_token": _setting("D360_API_KEY")},
                 params={"DriveFolderId": _setting("D360_DRIVE_FOLDER_ID"), "UserId": _setting("D360_USER_ID")},
                 files={"files": (filename, png_bytes, "image/png")}, timeout=60)
    except requests.RequestException as exc:
        raise DriveUploadError(f"the Drive request failed: {exc}") from exc
    if r.status_code >= 400:
        raise DriveUploadError(f"Drive returned HTTP {r.status_code}: {r.text[:300]}")
    try:
        body = r.json()
    except ValueError:
        body = None
    if isinstance(body, dict) and body.get("success") is False:
        raise DriveUploadError(f"Drive error: {body.get('errors') or body}")

    url = None
    if isinstance(body, dict):
        data = body.get("data")
        first = data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else data
        if isinstance(first, dict):
            url = first.get("file_url") or first.get("url") or first.get("public_url")
        url = url or body.get("file_url") or body.get("url")
    if url:
        return url, True
    return f"{PUBLIC_FILES_BASE}/{_setting('D360_DRIVE_PROJECT_ID')}/Images/Documentation/{filename}", False

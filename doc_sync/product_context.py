"""Which product reference files go into a prompt, by product line.

Each live workspace (core/workspaces.py) has a reference file describing
its concepts, terminology and a snapshot of its category structure. The
four DAP surfaces are DELTAS on one shared model: dap-core.md is the
concept model every DAP surface shares, and dap-web.md / dap-desktop.md /
dap-os.md / dap-mobile.md describe only what differs on that surface, so
each is always loaded together with dap-core.md. Product Analytics and
Whatfix Mirror are separate products with self-contained files.

Assessment picks the files for the ARTICLE's own workspace (read off the
live article), since in index discovery one change note can flag
articles in several workspaces; the change note's `product_line` is the
fallback, then DAP for Web — which is exactly what every prompt loaded
before this module existed, so a call that names no product line builds
the same prompt, byte for byte.
"""
from pathlib import Path

import workspaces

THIS_DIR = Path(__file__).resolve().parent  # the reference files live alongside this module

DEFAULT_PRODUCT_LINE = "DAP for Web"

PRODUCT_FILES = {
    "DAP for Web": ("dap-core.md", "dap-web.md"),
    "DAP for Desktop": ("dap-core.md", "dap-desktop.md"),
    "DAP on OS": ("dap-core.md", "dap-os.md"),
    "DAP for Mobile": ("dap-core.md", "dap-mobile.md"),
    "Product Analytics": ("product-analytics.md",),
    "Whatfix Mirror": ("mirror.md",),
}

# Kept in lockstep with the allow-list: a live workspace with no reference
# files would silently assess its articles against DAP for Web's.
if set(PRODUCT_FILES) != set(workspaces.names()):
    raise RuntimeError(
        f"product_context.PRODUCT_FILES {sorted(PRODUCT_FILES)} must cover exactly the live "
        f"workspaces {sorted(workspaces.names())}"
    )


def files_for(product_line=None):
    """The reference filenames for a product line (case-insensitive).
    An empty or unknown name falls back to DAP for Web — unknown ones
    with a printed note, so a typo is visible rather than silent."""
    target = (product_line or "").strip().lower()
    for name, files in PRODUCT_FILES.items():
        if name.lower() == target:
            return files
    if target:
        print(f"    (no product reference for product_line={product_line!r} — using {DEFAULT_PRODUCT_LINE!r}'s)")
    return PRODUCT_FILES[DEFAULT_PRODUCT_LINE]


def prompt_parts(product_line=None):
    """The product sections to append to a system prompt, one string per
    file, each headed `## <filename>` — the format both prompts used when
    these files were hardcoded. Missing files are skipped."""
    parts = []
    for filename in files_for(product_line):
        path = THIS_DIR / filename
        if path.exists():
            parts.append(f"\n\n## {filename}\n\n" + path.read_text())
    return parts


def product_line_of(article, change_note=None):
    """The product line an article belongs to: its own live workspace
    when the record carries one (every real article does), else the
    change note's `product_line`, else None (-> DAP for Web)."""
    name = workspaces.LIVE_WORKSPACES.get((article or {}).get("project_version_id"))
    if name:
        return name
    return (getattr(change_note, "product_line", "") or None) if change_note else None

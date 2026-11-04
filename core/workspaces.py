"""The Document360 workspaces (project versions) Doc Sync may read from or
write to: the six live, public product lines, and nothing else.

Each product line is a fully separate workspace with its own category
tree (see kb_search.py's note on the wrong-workspace bug of 2026-10-29),
and the account holds more than these six: Archived (the retired-article
sandbox `.env`'s D360_PROJECT_ID points at), plus Seek, Whatfix Playbooks,
Whatfix Use Cases and Whatfix Mobile Platform. Confirmed against a live
/ProjectVersions call on 2026-11-04.

This list is the guard, so it FAILS CLOSED: an id that is not here is
refused, whatever it is. That turns a whole class of bug — discovery
quietly reading the wrong workspace, or a live draft write landing in
Archived — into an error instead of a silent wrong answer. Ids, not
names, are the source of truth: a workspace renamed in Document360 keeps
its id, so a rename can never widen or narrow what's allowed.

Not applied to core/cli.py or core/articles.py: those are manual tools
that deliberately create and update articles in Archived.
"""

# id -> display name (`version_code_name` on /ProjectVersions).
LIVE_WORKSPACES = {
    "16262be3-befd-4410-bd95-7a9120d7dea9": "DAP for Web",
    "0ff1b42e-4356-44bc-8372-952945c2a1dd": "DAP for Desktop",
    "283cd074-b3b6-4178-acdb-d8898ad79481": "DAP on OS",
    "0ef024b7-1931-4477-8fff-3e72b0b4d4f8": "DAP for Mobile",
    "1216fcd2-4917-45a8-9f13-802e099ee913": "Product Analytics",
    "757b63a0-1b12-4526-879f-ecc8ab00cde7": "Whatfix Mirror",
}


class WorkspaceNotAllowed(RuntimeError):
    """Raised when a read or write targets a workspace outside LIVE_WORKSPACES."""


def is_live(version_id):
    return version_id in LIVE_WORKSPACES


def require_live(version_id, action):
    """Raise WorkspaceNotAllowed unless `version_id` is one of the six live
    workspaces. `action` is a short verb phrase for the message, e.g.
    "search" or "write a draft into"."""
    if not is_live(version_id):
        raise WorkspaceNotAllowed(
            f"Refusing to {action} Document360 workspace {version_id!r}: Doc Sync only "
            f"reads and writes the live product workspaces ({', '.join(names())})."
        )


def names():
    return list(LIVE_WORKSPACES.values())


def id_for_name(product_line):
    """A live workspace's id by its display name — case-insensitive,
    whitespace-trimmed. None for any name that isn't one of the six, so a
    non-live workspace ("Archived") can't be resolved even if it exists."""
    target = (product_line or "").strip().lower()
    for version_id, name in LIVE_WORKSPACES.items():
        if name.lower() == target:
            return version_id
    return None

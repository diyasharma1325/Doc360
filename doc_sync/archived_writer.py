"""The only way a ticket run writes to Document360: into scratch articles
in the ARCHIVED workspace that the writer listed for this run, never into
a live article. Modeled on the I2P backtest's write guard.

Live articles are only read. While doc-sync is still being trusted, each
corrected article goes into one of the Archived articles the writer
supplied (as portal links), overwriting it, so the real Document360 write
path can be exercised with no risk to published content.

The guard, all of it checked in code before a single write:

- ONLY THE LISTED ARTICLES. A write to any id that is not one of the
  writer's links is refused, whatever it is.
- ONLY THE ARCHIVED WORKSPACE. Each listed article is read first; one that
  lives in a live workspace (core/workspaces.py), or in any workspace whose
  name doesn't say "Archived", is refused, and nothing is written for any
  of them.
- NAME BEFORE OVERWRITE. describe() returns every target's current title,
  so the writer can confirm before anything is overwritten; ticket_run.py
  refuses to write without that confirmation. An overwrite has no undo.
- A DIRECT UPDATE, NEVER A FORK, NEVER A PUBLISH. Archived scratch articles
  are overwritten in place; the fork in core/articles.py stays for live
  articles, which nothing writes to yet.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))  # d360_client.py / workspaces.py

import workspaces
from d360_client import Document360Client, require_success


class ArchivedWriteRefused(RuntimeError):
    """A write the guard does not allow."""


def article_id_from_link(link):
    """The article id at the end of a portal link
    (https://portal.document360.io/<project>/document/archived/view/<id>),
    or the link itself if it is already a bare id."""
    return (link or "").strip().rstrip("/").split("/")[-1].split("?")[0]


class ArchivedTargets:
    """The Archived scratch articles a run may write into, in the order the
    writer listed them."""

    def __init__(self, links, client=None):
        self.client = client or Document360Client()
        self.links = [l.strip() for l in links or [] if l and l.strip()]
        self.ids = [article_id_from_link(l) for l in self.links]
        if len(set(self.ids)) != len(self.ids):
            raise ArchivedWriteRefused("The same Archived article is listed twice; each draft needs its own.")
        self._checked = None

    def describe(self):
        """Read every target and check it is in the Archived workspace.
        Returns [{id, link, title, version_name}] in order. Raises
        ArchivedWriteRefused, naming every problem, if any target fails;
        nothing is written either way."""
        if self._checked is not None:
            return self._checked
        names = {v.get("id"): (v.get("version_code_name") or v.get("name") or "")
                 for v in (self.client.list_project_versions().get("data") or [])}
        out, problems = [], []
        for aid, link in zip(self.ids, self.links):
            try:
                data = self.client.get_article(aid)["data"]
            except Exception as exc:
                problems.append(f"{link}: could not be read ({type(exc).__name__})")
                continue
            version_id = data.get("project_version_id")
            version_name = names.get(version_id, "")
            if workspaces.is_live(version_id):
                problems.append(f"{link}: is a LIVE article in {version_name or version_id}, not an Archived one")
            elif "archiv" not in version_name.lower():
                problems.append(f"{link}: is in workspace {version_name or version_id!r}, not Archived")
            else:
                out.append({"id": aid, "link": link, "title": data.get("title", ""), "version_name": version_name,
                            "category_id": data.get("category_id"), "version_number": data.get("version_number")})
        if problems:
            raise ArchivedWriteRefused("Refusing to write to any Archived target:\n  - " + "\n  - ".join(problems))
        self._checked = out
        return out

    def write(self, target_id, title, html):
        """Overwrite one listed Archived article with `title` and `html`.
        Refused unless describe() passed and `target_id` is one of the
        listed targets. Returns the target's link."""
        checked = {t["id"]: t for t in self.describe()}
        if target_id not in checked:
            raise ArchivedWriteRefused(f"{target_id!r} is not one of this run's Archived targets.")
        target = checked[target_id]
        current = self.client.get_article(target_id)["data"]  # fresh: version or category may have moved
        if workspaces.is_live(current.get("project_version_id")):
            raise ArchivedWriteRefused(f"{target_id!r} is now in a live workspace; refusing to write.")
        require_success(self.client.put(f"/Articles/{target_id}/en", json={
            "title": title,
            "category_id": current.get("category_id") or target["category_id"],
            "version_number": current.get("version_number") or target["version_number"] or 1,
            "content": html,
            "translation_option": "0",
        }), f"write Archived target {target_id}")
        return target["link"]

"""Create and update articles in the Document360 'Archived' workspace.

Workspace (project version), category, and user IDs come from .env — see
discover.py for how they were confirmed against the live API.

The one exception is fork_and_update(), doc-sync's live draft write: it
targets whichever workspace the article itself lives in, and only if
that is one of the live workspaces in workspaces.py (never Archived).
"""
import os

import workspaces
from d360_client import Document360Client, require_success

CONTENT_TYPE_BLOCK = 2  # matches the editor used by existing articles here


class ArticleService:
    def __init__(self, client=None):
        self.client = client or Document360Client()
        self.user_id = os.environ["D360_USER_ID"]
        self.category_id = os.environ["D360_FOLDER_ID"]
        self.project_version_id = self.client.project_id

    def create(self, title, content, category_id=None, order=0, publish=False,
               publish_message="Initial publish"):
        payload = {
            "title": title,
            "content": content,
            "category_id": category_id or self.category_id,
            "project_version_id": self.project_version_id,
            "user_id": self.user_id,
            "order": order,
            "content_type": CONTENT_TYPE_BLOCK,
        }
        result = self.client.post("/Articles", json=payload)
        article_id = result["data"]["id"]
        if publish:
            self.publish(article_id, version_number=1, message=publish_message)
        return result

    def update(self, article_id, title=None, content=None, lang_code="en",
               version_number=1, category_id=None):
        payload = {"version_number": version_number}
        if title is not None:
            payload["title"] = title
        if content is not None:
            payload["content"] = content
        if category_id is not None:
            payload["category_id"] = category_id
        return self.client.put(f"/Articles/{article_id}/{lang_code}", json=payload)

    def fork_and_update(self, article_id, content, current=None, lang_code="en"):
        """Write `content` into a NEW draft version of a live article,
        leaving its published version untouched:

          1. GET the article (or use `current`, an already-fetched
             get_article()["data"]) and refuse unless its own
             `project_version_id` is a live workspace — checked off the
             live record, not a cached index, since an article can move.
          2. PUT /Articles/{id}/fork -> a new draft version.
          3. PUT /Articles/{id}/{lang} into that new version.

        Does NOT check for an existing draft: draft_writer.py does that
        first and never calls this when one exists. Step 3's payload rules
        were confirmed live against this API: send `content`, not the
        deprecated `html_content`; leave out `content_type` (it 500s on an
        update); and `translation_option` must be the STRING "0".
        """
        current = current or self.client.get_article(article_id, lang_code)["data"]
        workspaces.require_live(current.get("project_version_id"), "write a draft into")
        base_version = current.get("version_number")
        category_id = current.get("category_id")
        if not base_version or not category_id:
            raise RuntimeError(
                f"Article {article_id} is missing version_number or category_id; refusing to fork it."
            )

        new_version = self.client.fork_article(article_id, base_version, self.user_id, lang_code)
        payload = {
            "category_id": category_id,
            "version_number": new_version,
            "content": content,
            "translation_option": "0",
        }
        if current.get("title"):
            payload["title"] = current["title"]
        require_success(
            self.client.put(f"/Articles/{article_id}/{lang_code}", json=payload),
            f"update forked draft of article {article_id}",
        )
        return {"data": {"id": article_id, "version_number": new_version}}

    def publish(self, article_id, version_number, message="Publishing via API"):
        payload = {
            "user_id": self.user_id,
            "version_number": version_number,
            "publish_message": message,
        }
        return self.client.post(f"/Articles/{article_id}/publish", json=payload)

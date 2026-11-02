"""Create and update articles in the Document360 'Archived' workspace.

Workspace (project version), category, and user IDs come from .env — see
discover.py for how they were confirmed against the live API.
"""
import os

from d360_client import Document360Client

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

    def publish(self, article_id, version_number, message="Publishing via API"):
        payload = {
            "user_id": self.user_id,
            "version_number": version_number,
            "publish_message": message,
        }
        return self.client.post(f"/Articles/{article_id}/publish", json=payload)

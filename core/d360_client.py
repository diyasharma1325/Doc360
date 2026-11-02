import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://apihub.document360.io/v2"


class Document360Error(RuntimeError):
    def __init__(self, response):
        self.response = response
        try:
            body = response.json()
        except ValueError:
            body = response.text
        super().__init__(f"Document360 API error {response.status_code}: {body}")


class Document360Client:
    def __init__(self, api_key=None, project_id=None):
        self.api_key = api_key or os.environ["D360_API_KEY"]
        self.project_id = project_id or os.environ["D360_PROJECT_ID"]
        self.session = requests.Session()
        self.session.headers.update(
            {"api_token": self.api_key, "Content-Type": "application/json"}
        )

    def _url(self, path):
        return f"{BASE_URL}{path}"

    def _request(self, method, path, **kwargs):
        response = self.session.request(method, self._url(path), timeout=30, **kwargs)
        if not response.ok:
            raise Document360Error(response)
        if response.content:
            return response.json()
        return None

    def get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)

    def post(self, path, json=None):
        return self._request("POST", path, json=json)

    def put(self, path, json=None):
        return self._request("PUT", path, json=json)

    # --- account/project-scoped helpers -----------------------------------------

    def list_project_versions(self):
        return self.get("/ProjectVersions")

    def list_team_accounts(self):
        return self.get("/Teams")

    def list_categories(self, project_version_id, params=None):
        return self.get(f"/ProjectVersions/{project_version_id}/categories", params=params)

    def list_articles(self, project_version_id, lang_code="en"):
        return self.get(
            f"/ProjectVersions/{project_version_id}/articles",
            params={"langCode": lang_code},
        )

    def get_article(self, article_id, lang_code="en"):
        # Path mirrors ArticleService.update()'s PUT path in articles.py.
        # Not yet verified against a live article for this workspace — the
        # doc-sync pipeline's draft-safety check depends on the response
        # actually containing `status`, `html_content`, and `version_number`
        # fields; confirm the shape before trusting that check.
        return self.get(f"/Articles/{article_id}/{lang_code}")

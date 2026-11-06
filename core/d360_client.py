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


class Document360LogicalError(RuntimeError):
    """Document360 answered HTTP 200 but with `success: false` in the body.
    The API reports many logical failures this way, so `response.ok` alone
    is not proof a call worked."""


def require_success(body, what):
    """Return `body`, or raise Document360LogicalError if it carries
    `success: false`. `what` names the call for the message. Only applied
    where a caller opts in, so existing helpers keep their behavior."""
    if isinstance(body, dict) and body.get("success") is False:
        raise Document360LogicalError(f"Document360 reported failure for {what}: {body.get('errors')}")
    return body


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
        # Verified live 2026-11-04 on published, pending-draft and
        # never-published articles: this path and `/Articles/{id}/{lang}`
        # return identical data. The response carries every field the
        # doc-sync pipeline relies on: `html_content`, `status` (0 = the
        # latest version is an unpublished draft, 3 = published),
        # `version_number` (the LATEST version, draft or not),
        # `public_version`, `latest_version`, `category_id` and
        # `project_version_id`. Unlike the category tree's per-article
        # `status`, which was stale on ~200 DAP for Web articles, this one
        # always agreed with the version numbers — read draft state here.
        body = self.get(f"/Articles/{article_id}", params={"langCode": lang_code})
        return require_success(body, f"GET article {article_id}")

    def fork_article(self, article_id, version_number, user_id, lang_code="en"):
        """Branch a new draft version off `version_number` and return the
        new version's number. The live version is left untouched until
        someone publishes the draft in Document360. PUT, not POST."""
        body = require_success(
            self.put(
                f"/Articles/{article_id}/fork",
                json={"version_number": version_number, "user_id": user_id, "lang_code": lang_code},
            ),
            f"fork article {article_id}",
        )
        new_version = (body.get("data") or {}).get("version_number")
        if not new_version:
            raise Document360LogicalError(
                f"Fork of article {article_id} did not return a new version number: {body!r}"
            )
        return new_version

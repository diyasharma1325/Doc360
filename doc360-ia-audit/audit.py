 #!/usr/bin/env python3
"""
Document360 Information Architecture Audit
--------------------------------------------
Pulls the full category/article tree from Document360's v2 API and flags
structural issues: orphaned categories, over-fragmented categories,
near-duplicate titles, stale published articles, and stuck drafts.

Usage:
    export DOC360_API_TOKEN="your-token-here"
    python3 audit.py [--stale-months 6] [--version-id <id>] [--out report.md]

If --version-id is omitted, the script uses the workspace's main version.
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher

import requests

BASE_URL = "https://apihub.document360.io/v2"
STATUS_MAP_ARTICLE = {0: "draft", 3: "published"}
STATUS_MAP_CATEGORY = {0: "draft", 3: "published"}
CONTENT_TYPE_MAP = {0: "markdown", 1: "wysiwyg", 2: "block"}

 
def api_get(path, token, params=None):
    resp = requests.get(
        f"{BASE_URL}{path}",
        headers={"api_token": token},
        params=params or {},
        timeout=30,
    )
    if resp.status_code == 429:
        retry_after = resp.headers.get("Retry-After", "unknown")
        sys.exit(f"Rate limited by Document360 API. Retry after {retry_after}s.")
    resp.raise_for_status()
    body = resp.json()
    if not body.get("success", True):
        sys.exit(f"API returned an error for {path}: {body.get('errors')}")
    return body.get("data")


def get_main_version_id(token, explicit_id=None):
    if explicit_id:
        return explicit_id
    versions = api_get("/projectversions", token)
    if not versions:
        sys.exit("No project versions returned — check the API token's workspace access.")
    for v in versions:
        if v.get("is_main_version"):
            return v["id"]
    return versions[0]["id"]


def fetch_tree(token, version_id):
    return api_get(
        f"/ProjectVersions/{version_id}/categories",
        token,
        params={"excludeArticles": "false", "includeCategoryDescription": "false"},
    )


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def walk(categories, path, depth, rows):
    """Flatten the recursive tree into per-category and per-article rows."""
    for cat in categories or []:
        cat_path = path + [cat.get("name") or "(untitled category)"]
        articles = cat.get("articles") or []
        children = cat.get("child_categories") or []
        rows["categories"].append({
            "id": cat.get("id"),
            "name": cat.get("name"),
            "path": " > ".join(cat_path),
            "depth": depth,
            "hidden": cat.get("hidden"),
            "article_count": len(articles),
            "child_count": len(children),
            "modified_at": parse_date(cat.get("modified_at")),
        })
        for art in articles:
            rows["articles"].append({
                "id": art.get("id"),
                "title": art.get("title") or "(untitled article)",
                "category_path": " > ".join(cat_path),
                "status": STATUS_MAP_ARTICLE.get(art.get("status"), art.get("status")),
                "hidden": art.get("hidden"),
                "created_at": parse_date(art.get("created_at")),
                "modified_at": parse_date(art.get("modified_at")),
            })
        walk(children, cat_path, depth + 1, rows)


def title_similarity(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def find_near_duplicate_titles(articles, threshold=0.87):
    pairs = []
    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            a, b = articles[i], articles[j]
            if a["category_path"] == b["category_path"] and a["title"] == b["title"]:
                continue  # exact same-category duplicates are caught separately
            sim = title_similarity(a["title"], b["title"])
            if sim >= threshold:
                pairs.append((a, b, sim))
    return sorted(pairs, key=lambda p: -p[2])


def build_report(rows, stale_months, generated_at):
    categories = rows["categories"]
    articles = rows["articles"]

    empty_categories = [c for c in categories if c["article_count"] == 0 and c["child_count"] == 0]
    thin_categories = [c for c in categories if c["article_count"] == 1]
    max_depth_categories = [c for c in categories if c["depth"] >= 2]  # D360 caps at 3 levels (0,1,2)

    now = generated_at
    stale_cutoff_days = stale_months * 30
    stale_published = []
    stuck_drafts = []
    for a in articles:
        ref_date = a["modified_at"] or a["created_at"]
        age_days = (now - ref_date).days if ref_date else None
        if a["status"] == "published" and age_days is not None and age_days > stale_cutoff_days:
            stale_published.append((a, age_days))
        if a["status"] == "draft" and age_days is not None and age_days > stale_cutoff_days:
            stuck_drafts.append((a, age_days))
    stale_published.sort(key=lambda p: -p[1])
    stuck_drafts.sort(key=lambda p: -p[1])

    dup_titles = find_near_duplicate_titles(articles)

    exact_dupes = defaultdict(list)
    for a in articles:
        exact_dupes[a["title"].lower().strip()].append(a)
    exact_dupes = {k: v for k, v in exact_dupes.items() if len(v) > 1}

    lines = []
    lines.append(f"# Document360 IA Audit Report")
    lines.append(f"Generated {now.strftime('%Y-%m-%d %H:%M UTC')}\n")
    lines.append("## Summary\n")
    lines.append(f"- Categories scanned: **{len(categories)}**")
    lines.append(f"- Articles scanned: **{len(articles)}**")
    lines.append(f"- Empty categories: **{len(empty_categories)}**")
    lines.append(f"- Single-article categories: **{len(thin_categories)}**")
    lines.append(f"- Categories at max nesting depth: **{len(max_depth_categories)}**")
    lines.append(f"- Exact duplicate titles: **{len(exact_dupes)}**")
    lines.append(f"- Near-duplicate title pairs: **{len(dup_titles)}**")
    lines.append(f"- Published articles untouched > {stale_months} months: **{len(stale_published)}**")
    lines.append(f"- Drafts untouched > {stale_months} months: **{len(stuck_drafts)}**\n")

    lines.append("## 1. Empty categories (no articles, no subcategories)")
    lines.append("Candidates to merge or remove — dead-end nodes in the nav tree.\n")
    if empty_categories:
        for c in empty_categories:
            lines.append(f"- `{c['path']}`" + (" *(hidden)*" if c["hidden"] else ""))
    else:
        lines.append("_None found._")
    lines.append("")

    lines.append("## 2. Single-article categories")
    lines.append("Categories holding exactly one article — often a sign of over-fragmented IA that could be flattened into a parent or sibling.\n")
    if thin_categories:
        for c in thin_categories:
            lines.append(f"- `{c['path']}`")
    else:
        lines.append("_None found._")
    lines.append("")

    lines.append("## 3. Exact duplicate article titles")
    lines.append("Same title used more than once — check whether these are true duplicates, stale forks, or legitimately reused names across categories.\n")
    if exact_dupes:
        for title, arts in exact_dupes.items():
            lines.append(f"- **{arts[0]['title']}**")
            for a in arts:
                lines.append(f"  - `{a['category_path']}`")
    else:
        lines.append("_None found._")
    lines.append("")

    lines.append("## 4. Near-duplicate article titles")
    lines.append("Titles that are very similar but not identical — possible overlapping or redundant content.\n")
    if dup_titles:
        for a, b, sim in dup_titles[:50]:
            lines.append(f"- ({sim:.0%} similar) **{a['title']}** (`{a['category_path']}`) <-> **{b['title']}** (`{b['category_path']}`)")
        if len(dup_titles) > 50:
            lines.append(f"- _...and {len(dup_titles) - 50} more (see CSV export)._")
    else:
        lines.append("_None found._")
    lines.append("")

    lines.append(f"## 5. Published articles not modified in {stale_months}+ months")
    lines.append("Highest-risk staleness: live content nobody has touched in a while.\n")
    if stale_published:
        for a, age in stale_published[:50]:
            lines.append(f"- **{a['title']}** (`{a['category_path']}`) — {age} days since last edit")
        if len(stale_published) > 50:
            lines.append(f"- _...and {len(stale_published) - 50} more (see CSV export)._")
    else:
        lines.append("_None found._")
    lines.append("")

    lines.append(f"## 6. Drafts stuck for {stale_months}+ months")
    lines.append("Started, never published, and never revisited — either finish them or archive them.\n")
    if stuck_drafts:
        for a, age in stuck_drafts[:50]:
            lines.append(f"- **{a['title']}** (`{a['category_path']}`) — {age} days since last edit")
        if len(stuck_drafts) > 50:
            lines.append(f"- _...and {len(stuck_drafts) - 50} more (see CSV export)._")
    else:
        lines.append("_None found._")
    lines.append("")

    lines.append("## 7. Categories at maximum nesting depth")
    lines.append("Document360 caps nesting at 3 levels — these categories are already at the ceiling, so any further subdivision needs a structural rethink, not another subcategory.\n")
    if max_depth_categories:
        for c in max_depth_categories:
            lines.append(f"- `{c['path']}`")
    else:
        lines.append("_None found._")
    lines.append("")

    return "\n".join(lines), {
        "empty_categories": empty_categories,
        "thin_categories": thin_categories,
        "exact_dupes": exact_dupes,
        "near_dupes": dup_titles,
        "stale_published": stale_published,
        "stuck_drafts": stuck_drafts,
    }


def write_csv(path, flagged):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["check", "item", "location", "detail"])
        for c in flagged["empty_categories"]:
            writer.writerow(["empty_category", c["name"], c["path"], ""])
        for c in flagged["thin_categories"]:
            writer.writerow(["single_article_category", c["name"], c["path"], ""])
        for title, arts in flagged["exact_dupes"].items():
            for a in arts:
                writer.writerow(["exact_duplicate_title", a["title"], a["category_path"], a["id"]])
        for a, b, sim in flagged["near_dupes"]:
            writer.writerow(["near_duplicate_title", a["title"], a["category_path"], f"~{b['title']} ({sim:.0%})"])
        for a, age in flagged["stale_published"]:
            writer.writerow(["stale_published", a["title"], a["category_path"], f"{age} days"])
        for a, age in flagged["stuck_drafts"]:
            writer.writerow(["stuck_draft", a["title"], a["category_path"], f"{age} days"])


def main():
    parser = argparse.ArgumentParser(description="Audit Document360 IA structure.")
    parser.add_argument("--stale-months", type=int, default=6, help="Months of inactivity to flag as stale (default: 6)")
    parser.add_argument("--version-id", default=None, help="Specific project version ID (default: main version)")
    parser.add_argument("--out", default="document360_audit_report.md", help="Output Markdown report path")
    parser.add_argument("--csv-out", default="document360_audit_flagged.csv", help="Output CSV path")
    args = parser.parse_args()

    token = os.environ.get("DOC360_API_TOKEN")
    if not token:
        sys.exit("Set DOC360_API_TOKEN in your environment before running this script.")

    print("Resolving project version...", file=sys.stderr)
    version_id = get_main_version_id(token, args.version_id)

    print(f"Fetching category tree for version {version_id}...", file=sys.stderr)
    tree = fetch_tree(token, version_id)

    rows = {"categories": [], "articles": []}
    walk(tree, [], 0, rows)
    print(f"Parsed {len(rows['categories'])} categories, {len(rows['articles'])} articles.", file=sys.stderr)

    report_md, flagged = build_report(rows, args.stale_months, datetime.now(timezone.utc))

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report_md)
    write_csv(args.csv_out, flagged)

    print(f"Report written to {args.out}", file=sys.stderr)
    print(f"Flagged items exported to {args.csv_out}", file=sys.stderr)


if __name__ == "__main__":
    main()

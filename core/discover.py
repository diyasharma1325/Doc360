"""Read-only discovery: confirm project version (workspace), category, and
team member IDs before wiring up article create/update. Makes no writes."""
import json
import os

from d360_client import Document360Client, Document360Error

TARGET_EMAIL = "diya.sharma@whatfix.com"


def show(label, value):
    print(f"\n=== {label} ===")
    print(json.dumps(value, indent=2)[:6000])

def main():
    client = Document360Client()
    configured_id = client.project_id
    print(f"Configured D360_PROJECT_ID: {configured_id}")
    print(f"Configured D360_FOLDER_ID:  {os.environ.get('D360_FOLDER_ID')}")

    versions = client.list_project_versions()
    matches = [v for v in versions.get("data", []) if v["id"] == configured_id]
    if matches:
        v = matches[0]
        print(
            f"\n>>> D360_PROJECT_ID matches workspace/version "
            f"'{v.get('version_code_name')}' (main={v.get('is_main_version')}, "
            f"beta={v.get('is_beta')})"
        )
    else:
        print("\n>>> WARNING: D360_PROJECT_ID not found among ProjectVersions!")
    show("All ProjectVersions (id, name)", [
        {"id": v["id"], "name": v.get("version_code_name"),
         "is_main_version": v.get("is_main_version")}
        for v in versions.get("data", [])
    ])

    if matches:
        try:
            cats = client.list_categories(configured_id)
            cat_ids = [c.get("id") for c in cats.get("data", [])]
            folder_id = os.environ.get("D360_FOLDER_ID")
            show("Categories in configured workspace", cats)
            print(f"\n>>> D360_FOLDER_ID present in this workspace's categories: "
                  f"{folder_id in cat_ids}")
        except Document360Error as e:
            show("Categories ERROR", str(e))

    try:
        teams = client.list_team_accounts()
        show("Team accounts", teams)
        team_list = teams.get("data") if isinstance(teams, dict) else teams
        email_match = None
        if isinstance(team_list, list):
            for t in team_list:
                if isinstance(t, dict) and t.get("email_id", "").lower() == TARGET_EMAIL.lower():
                    email_match = t
        print(f"\n>>> Team member matching {TARGET_EMAIL}: {email_match}")
    except Document360Error as e:
        show("Team accounts ERROR", str(e))


if __name__ == "__main__":
    main()

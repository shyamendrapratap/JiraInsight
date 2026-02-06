#!/usr/bin/env python3
"""
Sync CCEN Issues Directly
Try to get CCEN issues directly without going through sprints
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_loader import ConfigLoader
from jira_client import JiraClient
from database import DatabaseService
from tqdm import tqdm


def main():
    """Sync CCEN issues directly"""

    load_dotenv()

    config_loader = ConfigLoader()
    config = config_loader.load()

    jira_config = config.get("jira", {})
    jira_url = jira_config.get("urls", [])[0]
    jira_email = jira_config.get("email")
    jira_token = jira_config.get("token")

    jira_client = JiraClient(jira_url, jira_email, jira_token)

    print("\n" + "="*60)
    print("SYNC CCEN ISSUES DIRECTLY")
    print("="*60)

    if not jira_client.test_connection():
        print("\n❌ Cannot connect to JIRA!")
        sys.exit(1)

    print("\n✓ Connected to JIRA")

    db = DatabaseService("./data/kpi_data.db")

    # Try different project keys for CCEN
    project_keys = ["CCEN", "CCT"]

    print("\n📝 Trying to fetch CCEN/CCT issues...")

    sync_id = db.start_sync("ccen_direct", project_keys)
    issues_synced = 0

    for project in project_keys:
        print(f"\n  Trying project: {project}")

        # Try simple project query
        try:
            jql = f"project = {project} ORDER BY updated DESC"
            print(f"  JQL: {jql}")

            issues = jira_client.search_issues(jql, max_results=500)

            if issues:
                print(f"  ✓ Found {len(issues)} issues in {project}")

                for issue in tqdm(issues, desc=f"Syncing {project}"):
                    db.upsert_issue(issue)
                    issues_synced += 1
            else:
                print(f"  ⚠️  No issues found for {project}")

        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ Error: {error_msg[:150]}")

            # If project doesn't exist, API returns specific error
            if "does not exist" in error_msg.lower():
                print(f"  ℹ️  Project {project} does not exist in JIRA")

    db.complete_sync(sync_id, issues_synced, 0)

    # Show results
    print("\n" + "="*60)
    print("SYNC RESULTS")
    print("="*60)
    print(f"✓ Issues synced: {issues_synced}")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT project, COUNT(*) as count
            FROM issues
            GROUP BY project
            ORDER BY count DESC
        """)

        print("\nProjects in database:")
        for row in cursor.fetchall():
            print(f"  {row['project']}: {row['count']} issues")

    stats = db.get_stats()
    print(f"\nTotal Issues:  {stats['issues_count']}")
    print("="*60)

    if issues_synced > 0:
        print("\n✅ CCEN/CCT issues synced!")
        print("\n✓ Restart dashboard:")
        print("  lsof -ti:8050 | xargs kill -9")
        print("  python src/main.py --use-db")
    else:
        print("\n⚠️  No CCEN/CCT issues found.")
        print("\nPossible reasons:")
        print("  1. Project key might be different (not 'CCEN')")
        print("  2. Project doesn't exist in JIRA")
        print("  3. No permission to query the project")
        print("\nℹ️  Note: CCT already has 54 issues in database")
        print("   CCEN project might not exist or have different key")

    print()


if __name__ == "__main__":
    main()

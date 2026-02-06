#!/usr/bin/env python3
"""
Sync CCEN Kanban Board
Get issues from CCEN Kanban board (no sprints)
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
    """Sync CCEN Kanban board"""

    load_dotenv()

    config_loader = ConfigLoader()
    config = config_loader.load()

    jira_config = config.get("jira", {})
    jira_url = jira_config.get("urls", [])[0]
    jira_email = jira_config.get("email")
    jira_token = jira_config.get("token")

    jira_client = JiraClient(jira_url, jira_email, jira_token)

    print("\n" + "="*60)
    print("SYNC CCEN KANBAN BOARD")
    print("="*60)

    if not jira_client.test_connection():
        print("\n❌ Cannot connect to JIRA!")
        sys.exit(1)

    print("\n✓ Connected to JIRA")

    db = DatabaseService("./data/kpi_data.db")

    # CCEN Kanban board
    board_id = 13644
    board_name = "CCEN Kanban Board"

    print(f"\n📋 Board: {board_name} (ID: {board_id})")

    sync_id = db.start_sync("ccen_kanban", ["CCEN"])
    issues_synced = 0

    # Get issues from Kanban board
    print(f"\n📝 Fetching issues from Kanban board...")

    try:
        endpoint = f"/rest/agile/1.0/board/{board_id}/issue"

        # Get all pages
        start_at = 0
        max_results = 100

        while True:
            params = {
                "startAt": start_at,
                "maxResults": max_results
            }

            result = jira_client._make_request(endpoint, params=params)

            issues = result.get('issues', [])
            total = result.get('total', 0)

            if not issues:
                break

            print(f"  Fetching issues {start_at}-{start_at + len(issues)} of {total}...")

            for issue in tqdm(issues, desc="Syncing CCEN"):
                try:
                    db.upsert_issue(issue)
                    issues_synced += 1
                except Exception as e:
                    pass

            start_at += len(issues)

            if start_at >= total:
                break

            time.sleep(0.5)

    except Exception as e:
        print(f"❌ Error fetching board issues: {str(e)[:200]}")

    db.complete_sync(sync_id, issues_synced, 0)

    # Show results
    print("\n" + "="*60)
    print("SYNC RESULTS")
    print("="*60)
    print(f"✓ CCEN issues synced: {issues_synced}")

    # Show project breakdown
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # CCEN stats
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM issues
            WHERE project = 'CCEN'
            GROUP BY status
            ORDER BY count DESC
        """)

        print("\nCCEN status breakdown:")
        ccen_total = 0
        for row in cursor.fetchall():
            print(f"  {row['status']}: {row['count']}")
            ccen_total += row['count']
        print(f"  TOTAL: {ccen_total}")

        # Overall stats
        cursor.execute("""
            SELECT project, COUNT(*) as count
            FROM issues
            WHERE project IN ('CCT', 'CCEN', 'SCPX')
            GROUP BY project
            ORDER BY project
        """)

        print("\nAll projects:")
        for row in cursor.fetchall():
            print(f"  {row['project']}: {row['count']} issues")

    stats = db.get_stats()
    print(f"\nTotal Issues:  {stats['issues_count']}")
    print(f"Total Sprints: {stats['sprints_count']}")
    print("="*60)

    if issues_synced > 0:
        print("\n✅ CCEN data synced successfully!")
        print("\n✓ Restart dashboard to see CCEN data:")
        print("  lsof -ti:8050 | xargs kill -9")
        print("  python src/main.py --use-db")
    else:
        print("\n⚠️  No CCEN issues found on board.")

    print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Sync CCT Backlog
Get all issues from CCT board including backlog and current sprint
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import time

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_loader import ConfigLoader
from jira_client import JiraClient
from database import DatabaseService
from tqdm import tqdm


def main():
    """Sync CCT backlog and current issues"""

    load_dotenv()

    config_loader = ConfigLoader()
    config = config_loader.load()

    jira_config = config.get("jira", {})
    jira_url = jira_config.get("urls", [])[0]
    jira_email = jira_config.get("email")
    jira_token = jira_config.get("token")

    jira_client = JiraClient(jira_url, jira_email, jira_token)

    print("\n" + "="*60)
    print("SYNC CCT BACKLOG & ACTIVE ISSUES")
    print("="*60)

    if not jira_client.test_connection():
        print("\n❌ Cannot connect to JIRA!")
        sys.exit(1)

    print("\n✓ Connected to JIRA")

    db = DatabaseService("./data/kpi_data.db")

    board_id = 13679  # CCT Sprint Board
    print(f"\n📋 CCT Sprint Board (ID: {board_id})")

    sync_id = db.start_sync("cct_backlog", ["CCT"])
    issues_synced = 0

    # Get ALL issues from board (includes backlog, active sprints, etc.)
    print(f"\n📝 Fetching ALL issues from CCT board...")

    try:
        endpoint = f"/rest/agile/1.0/board/{board_id}/issue"

        start_at = 0
        max_results = 50

        while True:
            params = {
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "key,summary,status,issuetype,priority,assignee,reporter,created,updated,resolutiondate,labels,components,project,customfield_10016,customfield_10020"
            }

            print(f"  Fetching issues {start_at}...")

            result = jira_client._make_request(endpoint, params=params)

            issues = result.get('issues', [])
            total = result.get('total', 0)

            if not issues:
                break

            print(f"  ✓ Got {len(issues)} issues (total: {total})")

            for issue in issues:
                db.upsert_issue(issue)
                issues_synced += 1

            start_at += len(issues)

            if start_at >= total or start_at >= 500:  # Limit to 500 issues
                break

            time.sleep(0.3)

    except Exception as e:
        print(f"❌ Error: {str(e)[:200]}")

    db.complete_sync(sync_id, issues_synced, 0)

    # Show results
    print("\n" + "="*60)
    print("SYNC RESULTS")
    print("="*60)
    print(f"✓ CCT issues synced: {issues_synced}")

    # Show CCT status breakdown
    with db.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM issues
            WHERE project = 'CCT'
            GROUP BY status
            ORDER BY count DESC
        """)

        print("\nCCT status breakdown:")
        for row in cursor.fetchall():
            print(f"  {row['status']}: {row['count']}")

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM issues
            WHERE project = 'CCT' AND sprint_ids NOT LIKE '[]'
        """)

        sprint_assigned = cursor.fetchone()['count']
        print(f"\nCCT issues in sprints: {sprint_assigned}")

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

    print("\n✅ Sync complete!")
    print("\n✓ Restart dashboard to see updated CCT data:")
    print("  lsof -ti:8050 | xargs kill -9")
    print("  python src/main.py --use-db")
    print()


if __name__ == "__main__":
    main()

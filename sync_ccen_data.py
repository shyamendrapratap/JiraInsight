#!/usr/bin/env python3
"""
Sync CCEN Data
Specifically sync sprints and issues from CCEN boards
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
    """Sync CCEN data"""

    load_dotenv()

    # Load configuration
    config_loader = ConfigLoader()
    config = config_loader.load()

    # Initialize JIRA client
    jira_config = config.get("jira", {})
    jira_url = jira_config.get("urls", [])[0]
    jira_email = jira_config.get("email")
    jira_token = jira_config.get("token")

    jira_client = JiraClient(jira_url, jira_email, jira_token)

    print("\n" + "="*60)
    print("SYNC CCEN DATA")
    print("="*60)

    if not jira_client.test_connection():
        print("\n❌ Cannot connect to JIRA!")
        sys.exit(1)

    print("\n✓ Connected to JIRA")

    # Initialize database
    db = DatabaseService("./data/kpi_data.db")

    # Get CCEN boards from database
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, location_name
            FROM boards
            WHERE location_name LIKE '%CCEN%'
        """)
        ccen_boards = cursor.fetchall()

    if not ccen_boards:
        print("\n⚠️  No CCEN boards found in database!")
        print("Run: python sync_data.py --full")
        sys.exit(1)

    print(f"\n📋 Found {len(ccen_boards)} CCEN boards:")
    for board in ccen_boards:
        print(f"  - {board['name']} (ID: {board['id']})")

    # Sync sprints from CCEN boards
    print("\n🏃 Syncing sprints from CCEN boards...")
    sprints_synced = 0

    for board in ccen_boards:
        board_id = board['id']
        board_name = board['name']

        try:
            print(f"\n  Fetching sprints from {board_name}...")
            sprints = jira_client.get_sprints(board_id)

            if sprints:
                print(f"  ✓ Found {len(sprints)} sprints")
                for sprint in sprints:
                    sprint['originBoardName'] = board_name
                    db.upsert_sprint(sprint)
                    sprints_synced += 1
            else:
                print(f"  ⚠️  No sprints found")

        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")

    print(f"\n✓ Synced {sprints_synced} CCEN sprints")

    # Sync issues from CCEN sprints
    print("\n📝 Syncing issues from CCEN sprints...")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, board_id, board_name
            FROM sprints
            WHERE board_name LIKE '%CCEN%' OR board_name LIKE '%CCA%'
        """)
        ccen_sprints = cursor.fetchall()

    if not ccen_sprints:
        print("\n⚠️  No CCEN sprints found!")
        print("CCEN boards may not have any sprints configured.")
        return

    print(f"Found {len(ccen_sprints)} CCEN sprints")

    issues_synced = 0
    sync_id = db.start_sync("ccen_issues", ["CCEN", "CCT"])

    for sprint in tqdm(ccen_sprints, desc="Syncing CCEN issues"):
        sprint_id = sprint['id']

        try:
            endpoint = f"/rest/agile/1.0/sprint/{sprint_id}/issue"
            result = jira_client._make_request(endpoint, params={"maxResults": 100})

            issues = result.get('issues', [])
            for issue in issues:
                db.upsert_issue(issue)
                issues_synced += 1

            time.sleep(0.5)

        except Exception as e:
            pass  # Continue on errors

    db.complete_sync(sync_id, issues_synced, sprints_synced)

    # Show results
    print("\n" + "="*60)
    print("SYNC RESULTS")
    print("="*60)
    print(f"✓ Sprints synced: {sprints_synced}")
    print(f"✓ Issues synced: {issues_synced}")

    # Show updated stats
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
    print(f"Total Sprints: {stats['sprints_count']}")
    print("="*60)

    if issues_synced > 0:
        print("\n✅ CCEN data synced successfully!")
        print("\n✓ Restart dashboard to see CCEN data:")
        print("  lsof -ti:8050 | xargs kill -9")
        print("  python src/main.py --use-db")
    else:
        print("\n⚠️  No CCEN issues found.")
        print("CCEN boards may not have issues in sprints yet.")
        print("\nCheck JIRA to verify:")
        print("  - CCEN Board (ID: 13543)")
        print("  - CCA-Team-Board (ID: 13644)")

    print()


if __name__ == "__main__":
    main()

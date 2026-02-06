#!/usr/bin/env python3
"""
Sync Specific Boards
Sync data from CCT sprint board and CCEN Kanban board
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
    """Sync specific boards"""

    load_dotenv()

    config_loader = ConfigLoader()
    config = config_loader.load()

    jira_config = config.get("jira", {})
    jira_url = jira_config.get("urls", [])[0]
    jira_email = jira_config.get("email")
    jira_token = jira_config.get("token")

    jira_client = JiraClient(jira_url, jira_email, jira_token)

    print("\n" + "="*60)
    print("SYNC CCT AND CCEN BOARDS")
    print("="*60)

    if not jira_client.test_connection():
        print("\n❌ Cannot connect to JIRA!")
        sys.exit(1)

    print("\n✓ Connected to JIRA")

    db = DatabaseService("./data/kpi_data.db")

    # Specific board IDs from user
    boards_to_sync = [
        {"id": 13679, "name": "CCT Sprint Board", "project": "CCT"},
        {"id": 13644, "name": "CCEN Kanban Board", "project": "CCEN"}
    ]

    print(f"\n📋 Syncing {len(boards_to_sync)} boards...")

    sync_id = db.start_sync("specific_boards", ["CCT", "CCEN"])
    total_issues = 0
    total_sprints = 0

    for board in boards_to_sync:
        board_id = board['id']
        board_name = board['name']
        project = board['project']

        print(f"\n{'='*60}")
        print(f"Board: {board_name} (ID: {board_id})")
        print(f"Project: {project}")
        print('='*60)

        # First, sync the board info
        try:
            endpoint = f"/rest/agile/1.0/board/{board_id}"
            board_data = jira_client._make_request(endpoint)
            db.upsert_board(board_data)
            print(f"✓ Board info synced")
        except Exception as e:
            print(f"⚠️  Could not sync board info: {str(e)[:100]}")

        # Sync sprints from this board
        print(f"\n🏃 Syncing sprints...")
        try:
            sprints = jira_client.get_sprints(board_id)

            if sprints:
                print(f"✓ Found {len(sprints)} sprints")

                for sprint in sprints:
                    sprint['originBoardName'] = board_name
                    db.upsert_sprint(sprint)
                    total_sprints += 1

                # Sync issues from each sprint
                print(f"\n📝 Syncing issues from sprints...")

                for sprint in tqdm(sprints[:10], desc=f"{project} sprints"):  # First 10 sprints
                    sprint_id = sprint['id']

                    try:
                        endpoint = f"/rest/agile/1.0/sprint/{sprint_id}/issue"
                        result = jira_client._make_request(endpoint, params={"maxResults": 200})

                        issues = result.get('issues', [])
                        for issue in issues:
                            db.upsert_issue(issue)
                            total_issues += 1

                        time.sleep(0.3)

                    except Exception as e:
                        pass  # Continue on errors

            else:
                print(f"⚠️  No sprints found on this board")

                # For Kanban boards (no sprints), try to get issues directly from board
                print(f"\n📝 Trying to get issues from board (Kanban)...")
                try:
                    endpoint = f"/rest/agile/1.0/board/{board_id}/issue"
                    result = jira_client._make_request(endpoint, params={"maxResults": 500})

                    issues = result.get('issues', [])
                    if issues:
                        print(f"✓ Found {len(issues)} issues on board")

                        for issue in tqdm(issues, desc=f"{project} issues"):
                            db.upsert_issue(issue)
                            total_issues += 1

                except Exception as e:
                    print(f"❌ Could not get board issues: {str(e)[:150]}")

        except Exception as e:
            print(f"⚠️  Error syncing sprints: {str(e)[:150]}")

    db.complete_sync(sync_id, total_issues, total_sprints)

    # Show results
    print("\n" + "="*60)
    print("SYNC RESULTS")
    print("="*60)
    print(f"✓ Total issues synced: {total_issues}")
    print(f"✓ Total sprints synced: {total_sprints}")

    # Show project breakdown
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT project, status, COUNT(*) as count
            FROM issues
            WHERE project IN ('CCT', 'CCEN', 'SCPX')
            GROUP BY project, status
            ORDER BY project, count DESC
        """)

        current_project = None
        print("\nProject breakdown:")
        for row in cursor.fetchall():
            if row['project'] != current_project:
                current_project = row['project']
                print(f"\n  {current_project}:")
            print(f"    {row['status']}: {row['count']}")

    stats = db.get_stats()
    print(f"\nTotal Issues:  {stats['issues_count']}")
    print(f"Total Sprints: {stats['sprints_count']}")
    print("="*60)

    print("\n✅ Sync complete!")
    print("\n✓ Restart dashboard to see updated data:")
    print("  lsof -ti:8050 | xargs kill -9")
    print("  python src/main.py --use-db")
    print()


if __name__ == "__main__":
    main()

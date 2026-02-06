#!/usr/bin/env python3
"""
Sync Sprint Reports
Get completed vs committed data from sprint reports for Sprint Predictability
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import time
import json

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_loader import ConfigLoader
from jira_client import JiraClient
from database import DatabaseService
from tqdm import tqdm


def main():
    """Sync sprint reports for closed sprints"""

    load_dotenv()

    config_loader = ConfigLoader()
    config = config_loader.load()

    jira_config = config.get("jira", {})
    jira_url = jira_config.get("urls", [])[0]
    jira_email = jira_config.get("email")
    jira_token = jira_config.get("token")

    jira_client = JiraClient(jira_url, jira_email, jira_token)

    print("\n" + "="*60)
    print("SYNC SPRINT REPORTS")
    print("="*60)

    if not jira_client.test_connection():
        print("\n❌ Cannot connect to JIRA!")
        sys.exit(1)

    print("\n✓ Connected to JIRA")

    db = DatabaseService("./data/kpi_data.db")

    # Create sprint_reports table if it doesn't exist
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sprint_reports (
                sprint_id INTEGER PRIMARY KEY,
                board_id INTEGER,
                sprint_name TEXT,
                project TEXT,
                committed_count INTEGER,
                completed_count INTEGER,
                punted_count INTEGER,
                completion_rate REAL,
                report_data TEXT,
                synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # Get closed sprints for CCT and SCPX boards
    # Filter by sprint name patterns
    boards_to_sync = [
        {"id": 13679, "name": "CCT Sprint Board", "project": "CCT", "sprint_pattern": "Cloud-DR"},
        {"id": 2698, "name": "Ind-Scale-Perf", "project": "SCPX", "sprint_pattern": "Scale-Perf"}
    ]

    reports_synced = 0
    errors = 0

    for board in boards_to_sync:
        board_id = board['id']
        board_name = board['name']
        project = board['project']

        print(f"\n{'='*60}")
        print(f"Board: {board_name} (ID: {board_id})")
        print(f"Project: {project}")
        print('='*60)

        # Get ALL closed sprints and filter by sprint name pattern
        all_sprints = db.get_sprints(state="closed")
        sprint_pattern = board.get('sprint_pattern', '')
        # Filter to sprints from this project based on sprint name pattern
        sprints = [
            s for s in all_sprints
            if sprint_pattern.lower() in s.get('name', '').lower()
        ]

        if not sprints:
            print(f"⚠️  No closed sprints found for {board_name}")
            continue

        # Sort by end date and get recent ones
        sprints = sorted(sprints, key=lambda s: s.get('end_date', ''), reverse=True)[:15]

        print(f"✓ Found {len(sprints)} closed sprints to sync")

        # Sync sprint reports
        print(f"\n📊 Syncing sprint reports...")

        for sprint in tqdm(sprints, desc=f"{project} sprints"):
            sprint_id = sprint['id']
            sprint_name = sprint.get('name', 'Unknown')

            try:
                # Get sprint report
                endpoint = f"/rest/greenhopper/1.0/rapid/charts/sprintreport"
                params = {
                    "rapidViewId": board_id,
                    "sprintId": sprint_id
                }

                result = jira_client._make_request(endpoint, params=params, timeout=30)

                if result and 'contents' in result:
                    contents = result['contents']

                    # Extract metrics
                    completed_issues = contents.get('completedIssues', [])
                    not_completed = contents.get('issuesNotCompletedInCurrentSprint', [])
                    punted = contents.get('puntedIssues', [])

                    committed_count = len(completed_issues) + len(not_completed)
                    completed_count = len(completed_issues)
                    punted_count = len(punted)

                    # Store sprint report data in database
                    with db.get_connection() as conn:
                        cursor = conn.cursor()

                        completion_rate = round((completed_count / committed_count * 100) if committed_count > 0 else 0, 1)

                        cursor.execute("""
                            INSERT OR REPLACE INTO sprint_reports
                            (sprint_id, board_id, sprint_name, project, committed_count, completed_count, punted_count, completion_rate, report_data)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            sprint_id,
                            board_id,
                            sprint_name,
                            project,
                            committed_count,
                            completed_count,
                            punted_count,
                            completion_rate,
                            json.dumps(result)
                        ))

                    reports_synced += 1

                time.sleep(0.3)  # Rate limiting

            except Exception as e:
                errors += 1
                error_msg = str(e)
                if errors < 5:
                    print(f"\n⚠️  Error syncing {sprint_name}: {error_msg[:100]}")

    # Show results
    print("\n" + "="*60)
    print("SYNC RESULTS")
    print("="*60)
    print(f"✓ Sprint reports synced: {reports_synced}")
    print(f"⚠️  Errors: {errors}")

    # Show sprint report summary
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Overall stats
        cursor.execute("""
            SELECT
                project,
                COUNT(*) as sprint_count,
                AVG(completion_rate) as avg_completion_rate,
                SUM(committed_count) as total_committed,
                SUM(completed_count) as total_completed
            FROM sprint_reports
            GROUP BY project
            ORDER BY project
        """)

        print("\nSprint Predictability by Project:")
        for row in cursor.fetchall():
            print(f"\n  {row['project']}:")
            print(f"    Sprints Analyzed: {row['sprint_count']}")
            print(f"    Avg Completion Rate: {row['avg_completion_rate']:.1f}%")
            print(f"    Total Committed: {row['total_committed']}")
            print(f"    Total Completed: {row['total_completed']}")

        # Sample sprint reports
        cursor.execute("""
            SELECT sprint_name, project, committed_count, completed_count, completion_rate
            FROM sprint_reports
            ORDER BY synced_at DESC
            LIMIT 10
        """)

        print("\nSample Sprint Reports (10 most recent):")
        for row in cursor.fetchall():
            print(f"  {row['project']} - {row['sprint_name']}: {row['completed_count']}/{row['committed_count']} ({row['completion_rate']}%)")

    print("\n✅ Sprint report sync complete!")
    print("\n✓ Sprint Predictability calculations can now use sprint report data")
    print("\n✓ Restart dashboard to see updated KPIs:")
    print("  lsof -ti:8050 | xargs kill -9")
    print("  python src/main.py --use-db")
    print()


if __name__ == "__main__":
    main()

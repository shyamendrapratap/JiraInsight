#!/usr/bin/env python3
"""
Sync Active Sprints
Get current/active sprints with in-progress issues from CCT board
and CCEN Kanban board issues
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
    """Sync active sprints and current issues"""

    load_dotenv()

    config_loader = ConfigLoader()
    config = config_loader.load()

    jira_config = config.get("jira", {})
    jira_url = jira_config.get("urls", [])[0]
    jira_email = jira_config.get("email")
    jira_token = jira_config.get("token")

    jira_client = JiraClient(jira_url, jira_email, jira_token)

    print("\n" + "="*60)
    print("SYNC ACTIVE SPRINTS & CURRENT ISSUES")
    print("="*60)

    if not jira_client.test_connection():
        print("\n❌ Cannot connect to JIRA!")
        sys.exit(1)

    print("\n✓ Connected to JIRA")

    db = DatabaseService("./data/kpi_data.db")

    sync_id = db.start_sync("target_sprints", ["CCT", "CCEN"])
    total_issues = 0
    total_sprints = 0

    # ========================================
    # CCT Sprint Board - Active Sprints Only
    # ========================================
    print(f"\n{'='*60}")
    print(f"CCT Sprint Board (ID: 13679)")
    print('='*60)

    board_id = 13679

    # Get all sprints and filter for active ones
    print(f"\n🏃 Finding active sprints...")
    try:
        sprints = jira_client.get_sprints(board_id)

        if sprints:
            print(f"✓ Found {len(sprints)} total sprints")

            # Get active, future, and recent closed sprints for better KPI calculations
            target_sprints = [s for s in sprints if s.get('state') in ['active', 'future']]
            closed_sprints = [s for s in sprints if s.get('state') == 'closed']
            closed_sprints = sorted(closed_sprints, key=lambda x: x.get('endDate', ''), reverse=True)[:10]

            # Combine: active/future + 10 most recent closed
            target_sprints = target_sprints + closed_sprints

            if not target_sprints:
                print("⚠️  No sprints found")
                target_sprints = []

            print(f"✓ Targeting {len(target_sprints)} sprints:")
            print(f"  - Active/Future: {len(target_sprints)}")
            print(f"  - Recent Closed: {len(closed_sprints)}")
            for sprint in target_sprints[:5]:  # Show first 5
                state = sprint.get('state', 'unknown')
                name = sprint.get('name', 'Unknown')
                print(f"  - {name} ({state})")

            # Sync these sprints
            for sprint in target_sprints:
                sprint['originBoardName'] = 'CCT Sprint Board'
                db.upsert_sprint(sprint)
                total_sprints += 1

            # Sync issues from active sprints
            print(f"\n📝 Syncing issues from active sprints...")

            for sprint in tqdm(target_sprints, desc="CCT sprints"):
                sprint_id = sprint['id']
                sprint_name = sprint.get('name', 'Unknown')

                try:
                    endpoint = f"/rest/agile/1.0/sprint/{sprint_id}/issue"

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
                        total_issues_in_sprint = result.get('total', 0)

                        if not issues:
                            break

                        for issue in issues:
                            db.upsert_issue(issue)
                            total_issues += 1

                        start_at += len(issues)

                        if start_at >= total_issues_in_sprint:
                            break

                    time.sleep(0.3)

                except Exception as e:
                    print(f"\n⚠️  Error syncing sprint {sprint_name}: {str(e)[:100]}")

        else:
            print(f"⚠️  No sprints found on CCT board")

    except Exception as e:
        print(f"❌ Error accessing CCT sprints: {str(e)[:150]}")

    # ========================================
    # CCEN Kanban Board - Direct board issues
    # ========================================
    print(f"\n{'='*60}")
    print(f"CCEN Kanban Board (ID: 13644)")
    print('='*60)

    board_id = 13644

    print(f"\n📝 Fetching issues from Kanban board (with pagination)...")

    try:
        endpoint = f"/rest/agile/1.0/board/{board_id}/issue"

        # Get all pages with smaller batches
        start_at = 0
        max_results = 50  # Smaller batches to avoid timeouts
        ccen_issues = 0

        while True:
            params = {
                "startAt": start_at,
                "maxResults": max_results
            }

            print(f"  Fetching batch starting at {start_at}...")

            try:
                # Increase timeout for CCEN board
                result = jira_client._make_request(endpoint, params=params, timeout=60)

                issues = result.get('issues', [])
                total = result.get('total', 0)

                if not issues:
                    break

                print(f"  ✓ Got {len(issues)} issues (total: {total})")

                for issue in tqdm(issues, desc="CCEN issues"):
                    db.upsert_issue(issue)
                    total_issues += 1
                    ccen_issues += 1

                start_at += len(issues)

                if start_at >= total:
                    break

                time.sleep(0.5)  # Be gentle with API

            except Exception as e:
                error_msg = str(e)
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    print(f"  ⚠️  Timeout at position {start_at}, saving what we got...")
                    break
                else:
                    print(f"  ⚠️  Error: {error_msg[:100]}")
                    break

        print(f"\n✓ CCEN issues synced: {ccen_issues}")

    except Exception as e:
        print(f"❌ Error accessing CCEN board: {str(e)[:150]}")

    db.complete_sync(sync_id, total_issues, total_sprints)

    # Show results
    print("\n" + "="*60)
    print("SYNC RESULTS")
    print("="*60)
    print(f"✓ Total issues synced: {total_issues}")
    print(f"✓ Total sprints synced: {total_sprints}")

    # Show detailed project breakdown
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Overall project stats
        cursor.execute("""
            SELECT project, COUNT(*) as count
            FROM issues
            WHERE project IN ('CCT', 'CCEN', 'SCPX')
            GROUP BY project
            ORDER BY project
        """)

        print("\nProject totals:")
        for row in cursor.fetchall():
            print(f"  {row['project']}: {row['count']} issues")

        # CCT status breakdown
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM issues
            WHERE project = 'CCT'
            GROUP BY status
            ORDER BY count DESC
        """)

        print("\nCCT status breakdown:")
        cct_total = 0
        for row in cursor.fetchall():
            print(f"  {row['status']}: {row['count']}")
            cct_total += row['count']
        print(f"  TOTAL: {cct_total}")

        # CCEN status breakdown
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
        if ccen_total > 0:
            print(f"  TOTAL: {ccen_total}")
        else:
            print("  (No CCEN data)")

        # Check sprint assignments for CCT
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN sprint_ids != '[]' THEN 1 ELSE 0 END) as with_sprints
            FROM issues
            WHERE project = 'CCT'
        """)

        row = cursor.fetchone()
        print(f"\nCCT sprint assignments:")
        print(f"  Issues with sprints: {row['with_sprints']}/{row['total']}")

    stats = db.get_stats()
    print(f"\nDatabase totals:")
    print(f"  Issues:  {stats['issues_count']}")
    print(f"  Sprints: {stats['sprints_count']}")
    print("="*60)

    if total_issues > 0:
        print("\n✅ Sync complete!")
        print("\n✓ Restart dashboard to see updated data:")
        print("  lsof -ti:8050 | xargs kill -9")
        print("  python src/main.py --use-db")
    else:
        print("\n⚠️  No new issues synced.")

    print()


if __name__ == "__main__":
    main()

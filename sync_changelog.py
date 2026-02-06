#!/usr/bin/env python3
"""
Sync Issue Changelog
Get historical changelog for issues to reconstruct sprint history
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
    """Sync issue changelogs"""

    load_dotenv()

    config_loader = ConfigLoader()
    config = config_loader.load()

    jira_config = config.get("jira", {})
    jira_url = jira_config.get("urls", [])[0]
    jira_email = jira_config.get("email")
    jira_token = jira_config.get("token")

    jira_client = JiraClient(jira_url, jira_email, jira_token)

    print("\n" + "="*60)
    print("SYNC ISSUE CHANGELOGS")
    print("="*60)

    if not jira_client.test_connection():
        print("\n❌ Cannot connect to JIRA!")
        sys.exit(1)

    print("\n✓ Connected to JIRA")

    db = DatabaseService("./data/kpi_data.db")

    # Get all issues
    issues = db.get_issues()
    print(f"\n📝 Found {len(issues)} issues in database")

    # Filter to CCT and SCPX closed issues (most relevant for Sprint Predictability)
    target_issues = [
        i for i in issues
        if i['project'] in ['CCT', 'SCPX']
        and i['status'] in ['Done', 'Closed', 'Resolved']
    ]

    print(f"✓ Targeting {len(target_issues)} closed CCT/SCPX issues for changelog sync")
    print("  (These are most relevant for Sprint Predictability calculations)")

    changelogs_synced = 0
    errors = 0

    # Sync changelogs
    print("\n🔄 Syncing changelogs...")

    for issue in tqdm(target_issues[:500], desc="Syncing changelogs"):  # Limit to 500 to avoid long runtime
        try:
            # Get issue with full changelog
            endpoint = f"/rest/api/3/issue/{issue['key']}"
            params = {"expand": "changelog"}

            result = jira_client._make_request(endpoint, params=params, timeout=30)

            # Extract and store changelog
            changelog = result.get('changelog', {})
            histories = changelog.get('histories', [])

            if histories:
                # Store changelog entries
                for history in histories:
                    changelog_data = {
                        'issue_key': issue['key'],
                        'created': history.get('created'),
                        'author': history.get('author', {}).get('displayName', 'Unknown'),
                        'items': history.get('items', [])
                    }

                    # Store in database
                    with db.get_connection() as conn:
                        cursor = conn.cursor()

                        for item in changelog_data['items']:
                            cursor.execute("""
                                INSERT OR REPLACE INTO issue_changelog
                                (issue_key, changed_at, author, field, from_value, to_value)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                changelog_data['issue_key'],
                                changelog_data['created'],
                                changelog_data['author'],
                                item.get('field'),
                                item.get('fromString'),
                                item.get('toString')
                            ))

                changelogs_synced += 1

            # Rate limiting
            time.sleep(0.1)

        except Exception as e:
            errors += 1
            if errors < 5:  # Only print first few errors
                print(f"\n⚠️  Error syncing {issue['key']}: {str(e)[:100]}")

    # Show results
    print("\n" + "="*60)
    print("SYNC RESULTS")
    print("="*60)
    print(f"✓ Changelogs synced: {changelogs_synced}")
    print(f"⚠️  Errors: {errors}")

    # Check changelog entries
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Total entries
        cursor.execute("SELECT COUNT(*) as count FROM issue_changelog")
        total = cursor.fetchone()['count']
        print(f"\nTotal changelog entries: {total}")

        # Sprint changes
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM issue_changelog
            WHERE field = 'Sprint'
        """)
        sprint_changes = cursor.fetchone()['count']
        print(f"Sprint field changes: {sprint_changes}")

        # Sample sprint changes
        if sprint_changes > 0:
            cursor.execute("""
                SELECT issue_key, changed_at, from_value, to_value
                FROM issue_changelog
                WHERE field = 'Sprint'
                ORDER BY changed_at DESC
                LIMIT 5
            """)

            print("\nSample sprint changes:")
            for row in cursor.fetchall():
                print(f"  {row['issue_key']}: {row['from_value']} → {row['to_value']}")

    print("\n✅ Changelog sync complete!")
    print("\n✓ Sprint Predictability calculations can now use historical sprint data")
    print("\n✓ Restart dashboard to see updated KPIs:")
    print("  lsof -ti:8050 | xargs kill -9")
    print("  python src/main.py --use-db")
    print()


if __name__ == "__main__":
    main()

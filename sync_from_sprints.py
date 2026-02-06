#!/usr/bin/env python3
"""
Sync Issues from Sprints
Alternative approach - get issues from sprint API instead of JQL search
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
    """Sync issues from sprints"""

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
    print("SYNC ISSUES FROM SPRINTS")
    print("="*60)

    # Test connection
    if not jira_client.test_connection():
        print("\n❌ Cannot connect to JIRA!")
        sys.exit(1)

    print("\n✓ Connected to JIRA")

    # Initialize database
    db = DatabaseService("./data/kpi_data.db")

    # Get sprints from database
    sprints = db.get_sprints()
    print(f"\n📊 Found {len(sprints)} sprints in database")

    # Start sync
    sync_id = db.start_sync("sprint_issues", ["SCPX", "CCEN"])

    issues_synced = 0
    errors = []

    # Try to get issues from each sprint
    print("\n🔄 Fetching issues from sprints...")

    for sprint in tqdm(sprints[:10], desc="Processing sprints"):  # Try first 10 sprints
        sprint_id = sprint['id']
        sprint_name = sprint['name']

        try:
            # Use Agile API to get sprint issues
            endpoint = f"/rest/agile/1.0/sprint/{sprint_id}/issue"
            result = jira_client._make_request(endpoint, params={"maxResults": 100})

            issues = result.get('issues', [])

            if issues:
                print(f"\n✓ Found {len(issues)} issues in sprint {sprint_name}")

                for issue in issues:
                    try:
                        db.upsert_issue(issue)
                        issues_synced += 1
                    except Exception as e:
                        errors.append(f"Error saving {issue.get('key')}: {e}")

        except Exception as e:
            error_msg = f"Error fetching sprint {sprint_name}: {str(e)[:100]}"
            errors.append(error_msg)
            print(f"  ⚠️  {error_msg}")

    # Complete sync
    error_message = "\n".join(errors[:5]) if errors else None
    db.complete_sync(sync_id, issues_synced, 0, error_message)

    # Show results
    print("\n" + "="*60)
    print("SYNC RESULTS")
    print("="*60)
    print(f"✓ Issues synced: {issues_synced}")
    if errors:
        print(f"⚠️  Errors: {len(errors)}")
        print("\nFirst few errors:")
        for error in errors[:3]:
            print(f"  - {error}")

    # Show database stats
    stats = db.get_stats()
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    print(f"Total Issues:   {stats['issues_count']}")
    print(f"Total Sprints:  {stats['sprints_count']}")
    print(f"Total Boards:   {stats['boards_count']}")
    print(f"Projects:       {stats['projects_count']}")
    print("="*60)

    if issues_synced > 0:
        print("\n✅ Issues synced successfully!")
        print("\n✓ You can now run the dashboard:")
        print("  python src/main.py --use-db")
    else:
        print("\n⚠️  No issues were synced.")
        print("Your JIRA account may not have permission to access issue data.")
        print("\n💡 Use sample data instead:")
        print("  python generate_sample_data.py")
        print("  python src/main.py --use-db")

    print()


if __name__ == "__main__":
    main()

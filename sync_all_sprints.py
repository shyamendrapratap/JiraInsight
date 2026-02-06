#!/usr/bin/env python3
"""
Sync All Sprint Issues
Syncs issues from all sprints with better timeout handling
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
    """Sync issues from all sprints"""

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
    print("SYNC ALL SPRINT ISSUES")
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
    sync_id = db.start_sync("all_sprint_issues", ["SCPX", "CCEN"])

    issues_synced = 0
    sprints_processed = 0
    errors = []

    # Process all sprints
    print("\n🔄 Fetching issues from all sprints...")

    for sprint in tqdm(sprints, desc="Processing sprints"):
        sprint_id = sprint['id']
        sprint_name = sprint['name']

        try:
            # Use Agile API to get sprint issues
            endpoint = f"/rest/agile/1.0/sprint/{sprint_id}/issue"
            result = jira_client._make_request(endpoint, params={"maxResults": 100})

            issues = result.get('issues', [])

            if issues:
                for issue in issues:
                    try:
                        db.upsert_issue(issue)
                        issues_synced += 1
                    except Exception as e:
                        pass  # Silently handle duplicates

                sprints_processed += 1

            # Small delay to avoid overwhelming the API
            time.sleep(0.5)

        except Exception as e:
            error_msg = str(e)[:150]
            if "timeout" in error_msg.lower():
                errors.append(f"Timeout: {sprint_name}")
            else:
                errors.append(f"{sprint_name}: {error_msg}")

    # Complete sync
    error_message = "\n".join(errors[:10]) if errors else None
    db.complete_sync(sync_id, issues_synced, sprints_processed, error_message)

    # Show results
    print("\n" + "="*60)
    print("SYNC RESULTS")
    print("="*60)
    print(f"✓ Sprints processed: {sprints_processed}/{len(sprints)}")
    print(f"✓ Issues synced: {issues_synced}")
    if errors:
        print(f"⚠️  Errors/Timeouts: {len(errors)}")

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

    print("\n✅ Sync complete!")
    print("\n✓ Restart dashboard to see updated data:")
    print("  lsof -ti:8050 | xargs kill -9")
    print("  python src/main.py --use-db")
    print()


if __name__ == "__main__":
    main()

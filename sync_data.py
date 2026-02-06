#!/usr/bin/env python3
"""
Data Sync Script - Pull data from JIRA and store in local database
Run this script to refresh data from JIRA before viewing the dashboard
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_loader import ConfigLoader
from jira_client import JiraClient
from database import DatabaseService
from data_collector import DataCollector


def main():
    """Main sync script entry point"""

    # Load environment variables
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Sync data from JIRA to local database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full sync (recommended first time)
  python sync_data.py --full

  # Incremental sync (recent updates only)
  python sync_data.py

  # Sync with changelog (slower but more complete)
  python sync_data.py --full --with-changelog

  # Sync specific number of days
  python sync_data.py --full --days 30
        """
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Perform full sync (vs incremental)"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Number of days of history to fetch (default: 90)"
    )

    parser.add_argument(
        "--with-changelog",
        action="store_true",
        help="Include issue changelog (slower)"
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file"
    )

    parser.add_argument(
        "--db",
        type=str,
        default="./data/kpi_data.db",
        help="Path to database file"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show database statistics and exit"
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config_loader = ConfigLoader(args.config)
        config = config_loader.load()
    except Exception as e:
        print(f"\n❌ Configuration error: {e}")
        print("\nPlease check your configuration file and environment variables.")
        sys.exit(1)

    # Initialize database
    db = DatabaseService(args.db)

    # Show stats if requested
    if args.stats:
        stats = db.get_stats()
        print("\n" + "="*60)
        print("DATABASE STATISTICS")
        print("="*60)
        print(f"Total Issues:   {stats['issues_count']}")
        print(f"Total Sprints:  {stats['sprints_count']}")
        print(f"Total Boards:   {stats['boards_count']}")
        print(f"Projects:       {stats['projects_count']}")

        if stats['last_sync']:
            last_sync = stats['last_sync']
            print(f"\nLast Sync:")
            print(f"  Type:         {last_sync['sync_type']}")
            print(f"  Started:      {last_sync['started_at']}")
            print(f"  Completed:    {last_sync['completed_at']}")
            print(f"  Status:       {last_sync['status']}")
            print(f"  Issues:       {last_sync['issues_synced']}")
            print(f"  Sprints:      {last_sync['sprints_synced']}")
        else:
            print("\nNo sync history found")

        print("="*60 + "\n")
        sys.exit(0)

    # Initialize JIRA client
    jira_config = config.get("jira", {})
    jira_urls = jira_config.get("urls", [])

    if not jira_urls:
        print("\n❌ No JIRA URLs configured!")
        sys.exit(1)

    jira_url = jira_urls[0]
    jira_email = jira_config.get("email")
    jira_token = jira_config.get("token")

    jira_client = JiraClient(jira_url, jira_email, jira_token)

    # Test JIRA connection
    print("\n" + "="*60)
    print("JIRA Data Sync")
    print("="*60)
    print(f"\nJIRA URL: {jira_url}")
    print(f"Database: {args.db}")

    if not jira_client.test_connection():
        print("\n❌ Cannot connect to JIRA!")
        print("Please check your credentials in .env file")
        sys.exit(1)

    # Initialize data collector
    collector = DataCollector(jira_client, db, config)

    # Perform sync
    try:
        if args.full:
            print(f"\n🔄 Starting FULL sync (last {args.days} days)...")
            result = collector.sync_all_data(
                days_back=args.days,
                include_changelog=args.with_changelog
            )
        else:
            print("\n🔄 Starting INCREMENTAL sync (last 24 hours)...")
            result = collector.sync_recent_updates(hours_back=24)

        if result['success']:
            print("\n✅ Sync completed successfully!")
            print(f"\nSync ID: {result['sync_id']}")
            print(f"Issues synced: {result['issues_synced']}")
            if 'sprints_synced' in result:
                print(f"Sprints synced: {result['sprints_synced']}")

            # Show stats
            print("\n" + "="*60)
            stats = collector.get_sync_stats()
            print(f"Database now contains:")
            print(f"  Total Issues:  {stats['issues_count']}")
            print(f"  Total Sprints: {stats['sprints_count']}")
            print(f"  Total Boards:  {stats['boards_count']}")
            print(f"  Projects:      {stats['projects_count']}")
            print("="*60)

            print("\n✓ You can now run the dashboard:")
            print("  python src/main.py --use-db")
            print()

        else:
            print(f"\n❌ Sync failed: {result.get('error')}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Sync interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Sync error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Cleanup Sample Data
Removes sample/test data and keeps only real JIRA data
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import DatabaseService


def main():
    """Clean up sample data"""

    print("\n" + "="*60)
    print("CLEANUP SAMPLE DATA")
    print("="*60)

    db = DatabaseService("./data/kpi_data.db")

    # Show current stats
    stats = db.get_stats()
    print(f"\nCurrent database:")
    print(f"  Total Issues:  {stats['issues_count']}")
    print(f"  Total Sprints: {stats['sprints_count']}")
    print(f"  Total Boards:  {stats['boards_count']}")

    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Get count of sample data
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM issues
            WHERE raw_data LIKE '%Sample issue%' OR raw_data LIKE '%sample issue%'
        """)
        sample_count = cursor.fetchone()['count']

        print(f"\nSample data found: {sample_count} issues")

        if sample_count == 0:
            print("\n✓ No sample data found. Database is clean!")
            return

        # Delete sample data
        print(f"\n🗑️  Deleting {sample_count} sample issues...")
        cursor.execute("""
            DELETE FROM issues
            WHERE raw_data LIKE '%Sample issue%' OR raw_data LIKE '%sample issue%'
        """)

        # Also clean up related changelog entries
        cursor.execute("""
            DELETE FROM issue_changelog
            WHERE issue_key NOT IN (SELECT key FROM issues)
        """)

        conn.commit()

    # Show updated stats
    stats = db.get_stats()
    print("\n" + "="*60)
    print("CLEANED DATABASE")
    print("="*60)
    print(f"Total Issues:  {stats['issues_count']} (real JIRA data only)")
    print(f"Total Sprints: {stats['sprints_count']}")
    print(f"Total Boards:  {stats['boards_count']}")
    print(f"Projects:      {stats['projects_count']}")
    print("="*60)

    print("\n✅ Sample data removed!")
    print("\n✓ Restart dashboard to see cleaned data:")
    print("  lsof -ti:8050 | xargs kill -9")
    print("  python src/main.py --use-db")
    print()


if __name__ == "__main__":
    main()

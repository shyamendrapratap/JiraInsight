#!/usr/bin/env python3
"""
Cleanup Unwanted Projects
Removes OPR, IND, TFE projects from database
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import DatabaseService


def main():
    """Clean up unwanted projects"""

    print("\n" + "="*60)
    print("CLEANUP UNWANTED PROJECTS")
    print("="*60)

    db = DatabaseService("./data/kpi_data.db")

    # Show current stats
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Get project counts
        cursor.execute("""
            SELECT project, COUNT(*) as count
            FROM issues
            GROUP BY project
            ORDER BY count DESC
        """)

        print("\nCurrent projects:")
        projects_to_delete = []
        for row in cursor.fetchall():
            project = row['project']
            count = row['count']
            status = ""
            if project in ['OPR', 'IND', 'TFE']:
                status = " [WILL DELETE]"
                projects_to_delete.append(project)
            elif project in ['CCT', 'SCPX', 'CCEN']:
                status = " [KEEP]"
            print(f"  {project}: {count} issues{status}")

        if not projects_to_delete:
            print("\n✓ No unwanted projects found!")
            return

        # Delete unwanted projects
        print(f"\n🗑️  Deleting projects: {', '.join(projects_to_delete)}")

        for project in projects_to_delete:
            cursor.execute("DELETE FROM issues WHERE project = ?", (project,))
            deleted = cursor.rowcount
            print(f"  ✓ Deleted {deleted} issues from {project}")

        # Clean up orphaned changelog entries
        cursor.execute("""
            DELETE FROM issue_changelog
            WHERE issue_key NOT IN (SELECT key FROM issues)
        """)
        print(f"  ✓ Cleaned up {cursor.rowcount} orphaned changelog entries")

        conn.commit()

    # Show updated stats
    stats = db.get_stats()
    print("\n" + "="*60)
    print("CLEANED DATABASE")
    print("="*60)

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT project, COUNT(*) as count
            FROM issues
            GROUP BY project
            ORDER BY count DESC
        """)

        print("\nRemaining projects:")
        for row in cursor.fetchall():
            print(f"  {row['project']}: {row['count']} issues")

    print(f"\nTotal Issues:  {stats['issues_count']}")
    print(f"Total Sprints: {stats['sprints_count']}")
    print(f"Total Boards:  {stats['boards_count']}")
    print("="*60)

    print("\n✅ Cleanup complete!")
    print("\n✓ Restart dashboard to see cleaned data:")
    print("  lsof -ti:8050 | xargs kill -9")
    print("  python src/main.py --use-db")
    print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Sample Data Generator
Generates mock JIRA data for testing the dashboard
"""

import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import DatabaseService


def main():
    """Generate sample data"""

    print("\n" + "="*60)
    print("SAMPLE DATA GENERATOR")
    print("="*60)
    print("\nGenerating mock JIRA data for testing...")

    db = DatabaseService("./data/kpi_data.db")

    # Start a sync
    sync_id = db.start_sync("sample_data", ["SCPX", "CCEN"])

    issues_synced = 0
    sprints_synced = 0

    # Generate sample boards (already have 3)
    print("\n✓ Using existing 3 boards")

    # Generate sample sprints (already have 47)
    print("✓ Using existing 47 sprints")

    # Get sprints from database
    sprints = db.get_sprints()
    sprint_ids = [s['id'] for s in sprints[:10]]  # Use first 10 sprints

    # Generate sample issues
    print("\n📝 Generating sample issues...")

    projects = ["SCPX", "CCEN"]
    issue_types = ["Story", "Task", "Bug", "Epic"]
    statuses = ["Done", "Closed", "In Progress", "To Do"]
    priorities = ["High", "Medium", "Low"]
    labels_options = [
        ["feature_dev"],
        ["tech_debt"],
        ["reliability_perf"],
        ["ops_enablement"],
        ["unplanned"],
        ["feature_dev", "performance"],
        []
    ]

    issue_count = 0
    for project in projects:
        for i in range(1, 101):  # 100 issues per project
            issue_count += 1
            key = f"{project}-{i}"

            # Random dates
            created_date = datetime.now() - timedelta(days=random.randint(1, 90))
            updated_date = created_date + timedelta(days=random.randint(0, 30))
            resolved_date = None

            status = random.choice(statuses)
            if status in ["Done", "Closed"]:
                resolved_date = updated_date + timedelta(days=random.randint(1, 5))

            # Random sprint assignment (1-3 sprints per issue)
            num_sprints = random.choices([0, 1, 2, 3], weights=[20, 50, 20, 10])[0]
            issue_sprint_ids = random.sample(sprint_ids, min(num_sprints, len(sprint_ids))) if num_sprints > 0 else []

            issue_data = {
                'key': key,
                'fields': {
                    'project': {'key': project, 'name': f'{project} Project'},
                    'summary': f'Sample issue {i} for testing',
                    'description': 'This is a sample issue generated for testing',
                    'issuetype': {'name': random.choice(issue_types)},
                    'status': {'name': status},
                    'priority': {'name': random.choice(priorities)},
                    'assignee': {'displayName': f'User {random.randint(1, 10)}'},
                    'reporter': {'displayName': f'Reporter {random.randint(1, 5)}'},
                    'created': created_date.isoformat(),
                    'updated': updated_date.isoformat(),
                    'resolutiondate': resolved_date.isoformat() if resolved_date else None,
                    'resolution': {'name': 'Done'} if resolved_date else None,
                    'labels': random.choice(labels_options),
                    'components': [],
                    'sprint': [{'id': sid} for sid in issue_sprint_ids] if issue_sprint_ids else [],
                    'customfield_10016': random.choice([1, 2, 3, 5, 8, 13]),  # story points
                    'customfield_10020': [{'id': sid} for sid in issue_sprint_ids] if issue_sprint_ids else []
                }
            }

            db.upsert_issue(issue_data)

            # Add some changelog entries for completed issues
            if resolved_date and random.random() < 0.7:  # 70% of completed issues have changelog
                # In Progress transition
                in_progress_date = created_date + timedelta(days=random.randint(1, 5))
                db.insert_changelog_entry(key, {
                    'created': in_progress_date.isoformat(),
                    'author': {'displayName': f'User {random.randint(1, 10)}'},
                    'items': [{
                        'field': 'status',
                        'fromString': 'To Do',
                        'toString': 'In Progress'
                    }]
                })

                # Done transition
                db.insert_changelog_entry(key, {
                    'created': resolved_date.isoformat(),
                    'author': {'displayName': f'User {random.randint(1, 10)}'},
                    'items': [{
                        'field': 'status',
                        'fromString': 'In Progress',
                        'toString': status
                    }]
                })

                # Some issues were reopened
                if random.random() < 0.15:  # 15% reopened
                    reopen_date = resolved_date + timedelta(days=random.randint(1, 3))
                    db.insert_changelog_entry(key, {
                        'created': reopen_date.isoformat(),
                        'author': {'displayName': f'User {random.randint(1, 10)}'},
                        'items': [{
                            'field': 'status',
                            'fromString': status,
                            'toString': 'In Progress'
                        }]
                    })

            issues_synced += 1

    print(f"✓ Generated {issues_synced} sample issues")

    # Complete sync
    db.complete_sync(sync_id, issues_synced, sprints_synced)

    # Show stats
    stats = db.get_stats()
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    print(f"Total Issues:   {stats['issues_count']}")
    print(f"Total Sprints:  {stats['sprints_count']}")
    print(f"Total Boards:   {stats['boards_count']}")
    print(f"Projects:       {stats['projects_count']}")
    print("="*60)

    print("\n✅ Sample data generated successfully!")
    print("\n✓ You can now run the dashboard:")
    print("  python src/main.py --use-db")
    print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Project Discovery Script
Discovers available JIRA projects and recent issues
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_loader import ConfigLoader
from jira_client import JiraClient


def main():
    """Discover available projects"""

    load_dotenv()

    # Load configuration
    config_loader = ConfigLoader()
    config = config_loader.load()

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

    print("\n" + "="*60)
    print("JIRA PROJECT DISCOVERY")
    print("="*60)
    print(f"\nJIRA URL: {jira_url}")

    # Test connection
    if not jira_client.test_connection():
        print("\n❌ Cannot connect to JIRA!")
        sys.exit(1)

    print("\n✓ Connected to JIRA")

    # Try to get all boards first
    print("\n📋 Boards you have access to:")
    print("=" * 60)

    try:
        boards = jira_client.get_boards()
        if boards:
            for board in boards:
                location = board.get('location', {})
                project_key = location.get('projectKeyOrId', 'N/A')
                print(f"  - {board.get('name')} (ID: {board.get('id')}, Project: {project_key})")
        else:
            print("  No boards found")
    except Exception as e:
        print(f"  Error fetching boards: {e}")

    # Try to fetch recent issues without project filter
    print("\n📝 Trying to fetch recent issues (no project filter)...")
    print("=" * 60)

    try:
        # Try to get any issues at all
        jql = "order by updated DESC"
        issues = jira_client.search_issues(jql, max_results=10)

        if issues:
            print(f"\n✓ Found {len(issues)} recent issues:\n")

            projects = {}
            for issue in issues:
                project_key = issue.get('fields', {}).get('project', {}).get('key')
                project_name = issue.get('fields', {}).get('project', {}).get('name')
                issue_key = issue.get('key')
                summary = issue.get('fields', {}).get('summary', '')

                if project_key:
                    if project_key not in projects:
                        projects[project_key] = {'name': project_name, 'issues': []}
                    projects[project_key]['issues'].append(f"{issue_key}: {summary[:50]}")

            print("\n📊 Projects with recent activity:")
            print("=" * 60)
            for project_key, data in projects.items():
                print(f"\n  Project: {project_key} - {data['name']}")
                print(f"  Issues found: {len(data['issues'])}")
                for issue in data['issues'][:3]:
                    print(f"    - {issue}")

            print("\n\n💡 To use these projects, update config/config.yaml:")
            print("="*60)
            print("projects:")
            print("  project_keys:")
            for project_key in projects.keys():
                print(f"    - \"{project_key}\"")
            print()

        else:
            print("  No issues found")

    except Exception as e:
        print(f"  Error fetching issues: {e}")

    print("\n" + "="*60)
    print("Discovery complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

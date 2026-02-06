#!/usr/bin/env python3
"""
Test Sprint Report API
Check if we can get sprint reports with completed vs committed data
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import json

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_loader import ConfigLoader
from jira_client import JiraClient


def main():
    """Test sprint report API"""

    load_dotenv()

    config_loader = ConfigLoader()
    config = config_loader.load()

    jira_config = config.get("jira", {})
    jira_url = jira_config.get("urls", [])[0]
    jira_email = jira_config.get("email")
    jira_token = jira_config.get("token")

    jira_client = JiraClient(jira_url, jira_email, jira_token)

    print("\n" + "="*60)
    print("TEST SPRINT REPORT API")
    print("="*60)

    if not jira_client.test_connection():
        print("\n❌ Cannot connect to JIRA!")
        sys.exit(1)

    print("\n✓ Connected to JIRA")

    # Try closed CCT sprint
    board_id = 13679
    sprint_id = 26663  # Cloud-DR-sprint28 (closed)

    print(f"\n📊 Testing Sprint Report API")
    print(f"Board ID: {board_id}")
    print(f"Sprint ID: {sprint_id} (Cloud-DR-sprint28)")

    # Try different sprint report endpoints
    endpoints_to_try = [
        f"/rest/greenhopper/1.0/rapid/charts/sprintreport?rapidViewId={board_id}&sprintId={sprint_id}",
        f"/rest/agile/1.0/board/{board_id}/sprint/{sprint_id}",
        f"/rest/agile/1.0/sprint/{sprint_id}",
    ]

    for endpoint in endpoints_to_try:
        print(f"\n{'='*60}")
        print(f"Trying: {endpoint}")
        print('='*60)

        try:
            result = jira_client._make_request(endpoint, timeout=30)

            if result:
                print("✓ Success!")
                print("\nResponse keys:")
                if isinstance(result, dict):
                    for key in result.keys():
                        print(f"  - {key}")

                    # Check for sprint report specific data
                    if 'contents' in result:
                        contents = result['contents']
                        print(f"\n📊 Sprint Report Contents:")
                        if 'completedIssues' in contents:
                            completed = contents['completedIssues']
                            print(f"  Completed Issues: {len(completed)}")
                            if completed:
                                print(f"    Sample: {completed[0].get('key', 'N/A')}")

                        if 'issuesNotCompletedInCurrentSprint' in contents:
                            not_completed = contents['issuesNotCompletedInCurrentSprint']
                            print(f"  Not Completed: {len(not_completed)}")

                        if 'puntedIssues' in contents:
                            punted = contents['puntedIssues']
                            print(f"  Punted/Removed: {len(punted)}")

                        if 'issuesCompletedInAnotherSprint' in contents:
                            other_sprint = contents['issuesCompletedInAnotherSprint']
                            print(f"  Completed in Another Sprint: {len(other_sprint)}")

                    # Check for basic sprint info
                    if 'name' in result:
                        print(f"\n📋 Sprint Info:")
                        print(f"  Name: {result.get('name')}")
                        print(f"  State: {result.get('state')}")
                        print(f"  Start: {result.get('startDate', 'N/A')[:10]}")
                        print(f"  End: {result.get('endDate', 'N/A')[:10]}")

                    # Print full response for first successful endpoint
                    print(f"\n📄 Full Response (truncated):")
                    response_str = json.dumps(result, indent=2)
                    print(response_str[:1000])
                    if len(response_str) > 1000:
                        print("\n... (truncated)")

                    break  # Success, no need to try other endpoints

        except Exception as e:
            print(f"❌ Error: {str(e)[:200]}")

    print("\n" + "="*60)


if __name__ == "__main__":
    main()

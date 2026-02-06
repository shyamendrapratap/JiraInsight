"""
Data Collector - Fetches data from JIRA and stores in database
Handles incremental syncs and error recovery
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from tqdm import tqdm

from jira_client import JiraClient
from database import DatabaseService


class DataCollector:
    """Collects data from JIRA and stores in database"""

    def __init__(self, jira_client: JiraClient, db_service: DatabaseService, config: Dict):
        """
        Initialize data collector

        Args:
            jira_client: JIRA API client
            db_service: Database service
            config: Configuration dictionary
        """
        self.jira = jira_client
        self.db = db_service
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.projects = config.get("projects", {}).get("project_keys", [])

    def sync_all_data(self, days_back: int = 90, include_changelog: bool = False):
        """
        Sync all data from JIRA to database

        Args:
            days_back: Number of days of history to fetch
            include_changelog: Whether to fetch issue changelog (slower)

        Returns:
            Dictionary with sync statistics
        """
        sync_id = self.db.start_sync("full", self.projects)
        self.logger.info(f"Starting full data sync (sync_id: {sync_id})")

        issues_synced = 0
        sprints_synced = 0
        error_message = None

        try:
            # Step 1: Sync boards
            print("\n📋 Step 1/4: Syncing boards...")
            boards = self._sync_boards()
            print(f"✓ Synced {len(boards)} boards")

            # Step 2: Sync sprints
            print("\n🏃 Step 2/4: Syncing sprints...")
            sprints_synced = self._sync_sprints(boards)
            print(f"✓ Synced {sprints_synced} sprints")

            # Step 3: Sync issues
            print("\n📝 Step 3/4: Syncing issues...")
            issues_synced = self._sync_issues(days_back)
            print(f"✓ Synced {issues_synced} issues")

            # Step 4: Sync changelog (optional)
            if include_changelog:
                print("\n📜 Step 4/4: Syncing issue changelog...")
                self._sync_changelog()
                print("✓ Changelog synced")
            else:
                print("\n⏭️  Step 4/4: Skipping changelog (use --with-changelog to include)")

            self.db.complete_sync(sync_id, issues_synced, sprints_synced)

            print(f"\n✅ Sync completed successfully!")
            print(f"   - Issues synced: {issues_synced}")
            print(f"   - Sprints synced: {sprints_synced}")

            return {
                'success': True,
                'sync_id': sync_id,
                'issues_synced': issues_synced,
                'sprints_synced': sprints_synced
            }

        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Sync failed: {e}", exc_info=True)
            self.db.complete_sync(sync_id, issues_synced, sprints_synced, error_message)

            print(f"\n❌ Sync failed: {e}")

            return {
                'success': False,
                'sync_id': sync_id,
                'issues_synced': issues_synced,
                'sprints_synced': sprints_synced,
                'error': error_message
            }

    def _sync_boards(self) -> List[Dict]:
        """
        Sync boards from JIRA

        Returns:
            List of board dictionaries
        """
        all_boards = []

        for project in self.projects:
            try:
                boards = self.jira.get_boards(project_key=project)
                for board in boards:
                    self.db.upsert_board(board)
                    all_boards.append(board)
                    self.logger.info(f"Synced board: {board.get('name')} (ID: {board.get('id')})")
            except Exception as e:
                self.logger.warning(f"Could not fetch boards for project {project}: {e}")

        # Also try to get all boards (without project filter) as fallback
        if not all_boards:
            try:
                boards = self.jira.get_boards()
                for board in boards:
                    self.db.upsert_board(board)
                    all_boards.append(board)
            except Exception as e:
                self.logger.warning(f"Could not fetch boards: {e}")

        return all_boards

    def _sync_sprints(self, boards: List[Dict]) -> int:
        """
        Sync sprints from boards

        Args:
            boards: List of board dictionaries

        Returns:
            Number of sprints synced
        """
        sprint_count = 0

        for board in boards:
            board_id = board.get('id')
            board_name = board.get('name')

            try:
                sprints = self.jira.get_sprints(board_id)
                for sprint in sprints:
                    # Add board name to sprint data
                    sprint['originBoardName'] = board_name
                    self.db.upsert_sprint(sprint)
                    sprint_count += 1
                    self.logger.info(f"Synced sprint: {sprint.get('name')} (Board: {board_name})")
            except Exception as e:
                self.logger.warning(f"Could not fetch sprints for board {board_name}: {e}")

        return sprint_count

    def _sync_issues(self, days_back: int = 90) -> int:
        """
        Sync issues from JIRA

        Args:
            days_back: Number of days of history to fetch

        Returns:
            Number of issues synced
        """
        issue_count = 0

        # Try multiple approaches to fetch issues
        # Approach 1: Try each project separately
        for project in self.projects:
            try:
                date_cutoff = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                jql = f"project = {project} AND updated >= '{date_cutoff}' ORDER BY updated DESC"

                self.logger.info(f"Fetching issues for project {project} with JQL: {jql}")

                fields = [
                    'key', 'summary', 'description', 'issuetype', 'status', 'priority',
                    'assignee', 'reporter', 'created', 'updated', 'resolutiondate', 'resolution',
                    'labels', 'components', 'project', 'customfield_10016',  # story points
                    'customfield_10020'  # sprint field
                ]

                issues = self.jira.search_issues(jql, fields=fields, max_results=5000)

                if issues:
                    print(f"Found {len(issues)} issues in project {project}...")
                    for issue in tqdm(issues, desc=f"Syncing {project}"):
                        try:
                            self.db.upsert_issue(issue)
                            issue_count += 1
                        except Exception as e:
                            self.logger.error(f"Error syncing issue {issue.get('key')}: {e}")
                else:
                    print(f"No issues found in project {project}")

            except Exception as e:
                self.logger.warning(f"Could not fetch issues for project {project}: {e}")

                # Try even simpler query for this project
                try:
                    simple_jql = f"project = {project} ORDER BY updated DESC"
                    self.logger.info(f"Trying simpler query: {simple_jql}")
                    issues = self.jira.search_issues(simple_jql, max_results=500)

                    if issues:
                        print(f"Found {len(issues)} issues in {project} (simple query)...")
                        for issue in tqdm(issues, desc=f"Syncing {project}"):
                            try:
                                self.db.upsert_issue(issue)
                                issue_count += 1
                            except Exception as e:
                                self.logger.error(f"Error syncing issue {issue.get('key')}: {e}")

                except Exception as e:
                    self.logger.error(f"All queries failed for project {project}: {e}")

        # Approach 2: If no issues were found, try getting ALL recent issues (no project filter)
        if issue_count == 0:
            try:
                self.logger.info("No issues found per project, trying global search...")
                date_cutoff = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                jql = f"updated >= '{date_cutoff}' ORDER BY updated DESC"

                issues = self.jira.search_issues(jql, max_results=1000)

                if issues:
                    print(f"Found {len(issues)} issues (global search)...")
                    for issue in tqdm(issues, desc="Syncing issues"):
                        try:
                            self.db.upsert_issue(issue)
                            issue_count += 1
                        except Exception as e:
                            self.logger.error(f"Error syncing issue {issue.get('key')}: {e}")

            except Exception as e:
                self.logger.error(f"Global search also failed: {e}")

        return issue_count

    def _sync_changelog(self):
        """
        Sync changelog for all issues in database

        Note: This is expensive and slow - only use when needed
        """
        issues = self.db.get_issues(limit=None)

        print(f"Syncing changelog for {len(issues)} issues...")

        for issue in tqdm(issues, desc="Syncing changelog"):
            try:
                issue_key = issue['key']
                changelog = self.jira.get_issue_changelog(issue_key)

                for entry in changelog:
                    self.db.insert_changelog_entry(issue_key, entry)

            except Exception as e:
                self.logger.warning(f"Could not fetch changelog for {issue_key}: {e}")

    def sync_recent_updates(self, hours_back: int = 24) -> Dict:
        """
        Sync only recently updated issues (incremental sync)

        Args:
            hours_back: Number of hours to look back

        Returns:
            Sync statistics
        """
        sync_id = self.db.start_sync("incremental", self.projects)
        self.logger.info(f"Starting incremental sync (sync_id: {sync_id})")

        issues_synced = 0
        error_message = None

        try:
            projects_str = ", ".join(self.projects)
            time_cutoff = (datetime.now() - timedelta(hours=hours_back)).strftime('%Y-%m-%d %H:%M')

            jql = f"project in ({projects_str}) AND updated >= '{time_cutoff}' ORDER BY updated DESC"

            issues = self.jira.search_issues(jql, max_results=1000)

            for issue in issues:
                self.db.upsert_issue(issue)
                issues_synced += 1

            self.db.complete_sync(sync_id, issues_synced, 0)

            return {
                'success': True,
                'sync_id': sync_id,
                'issues_synced': issues_synced
            }

        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Incremental sync failed: {e}", exc_info=True)
            self.db.complete_sync(sync_id, issues_synced, 0, error_message)

            return {
                'success': False,
                'sync_id': sync_id,
                'issues_synced': issues_synced,
                'error': error_message
            }

    def get_sync_stats(self) -> Dict:
        """
        Get sync statistics

        Returns:
            Dictionary with sync stats
        """
        return self.db.get_stats()

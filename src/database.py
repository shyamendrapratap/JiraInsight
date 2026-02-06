"""
Database service for storing and retrieving JIRA data
Uses SQLite for simple, local data persistence
"""

import sqlite3
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager


class DatabaseService:
    """Service for managing JIRA data in SQLite database"""

    def __init__(self, db_path: str = "./data/kpi_data.db"):
        """
        Initialize database service

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_schema()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Issues table - stores all JIRA issues
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS issues (
                    key TEXT PRIMARY KEY,
                    project TEXT NOT NULL,
                    summary TEXT,
                    description TEXT,
                    issue_type TEXT,
                    status TEXT,
                    priority TEXT,
                    assignee TEXT,
                    reporter TEXT,
                    created TEXT,
                    updated TEXT,
                    resolved TEXT,
                    resolution TEXT,
                    labels TEXT,  -- JSON array
                    components TEXT,  -- JSON array
                    sprint_ids TEXT,  -- JSON array of sprint IDs
                    story_points REAL,
                    raw_data TEXT,  -- Full JSON of issue
                    synced_at TEXT NOT NULL
                )
            """)

            # Sprints table - stores sprint information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sprints (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    board_id INTEGER,
                    board_name TEXT,
                    state TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    complete_date TEXT,
                    goal TEXT,
                    raw_data TEXT,
                    synced_at TEXT NOT NULL
                )
            """)

            # Issue changelog table - stores issue history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS issue_changelog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_key TEXT NOT NULL,
                    created TEXT NOT NULL,
                    author TEXT,
                    field TEXT,
                    from_value TEXT,
                    to_value TEXT,
                    FOREIGN KEY (issue_key) REFERENCES issues (key)
                )
            """)

            # Boards table - stores board information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS boards (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT,
                    location_type TEXT,
                    location_name TEXT,
                    synced_at TEXT NOT NULL
                )
            """)

            # Sync metadata table - tracks data sync status
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_type TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL,
                    projects TEXT,  -- JSON array
                    issues_synced INTEGER DEFAULT 0,
                    sprints_synced INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """)

            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_issues_project ON issues(project)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_issues_created ON issues(created)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_issues_resolved ON issues(resolved)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sprints_board ON sprints(board_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sprints_state ON sprints(state)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_changelog_issue ON issue_changelog(issue_key)")

            self.logger.info(f"Database initialized at {self.db_path}")

    def start_sync(self, sync_type: str, projects: List[str]) -> int:
        """
        Start a new sync operation

        Args:
            sync_type: Type of sync (full, incremental, etc.)
            projects: List of project keys being synced

        Returns:
            Sync ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_metadata (sync_type, started_at, status, projects)
                VALUES (?, ?, 'running', ?)
            """, (sync_type, datetime.now().isoformat(), json.dumps(projects)))
            return cursor.lastrowid

    def complete_sync(self, sync_id: int, issues_synced: int = 0, sprints_synced: int = 0, error: str = None):
        """
        Mark sync operation as complete

        Args:
            sync_id: Sync operation ID
            issues_synced: Number of issues synced
            sprints_synced: Number of sprints synced
            error: Error message if sync failed
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            status = 'failed' if error else 'completed'
            cursor.execute("""
                UPDATE sync_metadata
                SET completed_at = ?, status = ?, issues_synced = ?, sprints_synced = ?, error_message = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), status, issues_synced, sprints_synced, error, sync_id))

    def upsert_issue(self, issue_data: Dict):
        """
        Insert or update an issue

        Args:
            issue_data: Issue data dictionary from JIRA
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            fields = issue_data.get('fields', {})
            key = issue_data.get('key')

            # Extract sprint IDs
            sprint_field = fields.get('sprint') or fields.get('customfield_10020', [])
            sprint_ids = []
            if sprint_field:
                if isinstance(sprint_field, list):
                    sprint_ids = [s.get('id') for s in sprint_field if isinstance(s, dict) and s.get('id')]
                elif isinstance(sprint_field, dict):
                    sprint_ids = [sprint_field.get('id')]

            cursor.execute("""
                INSERT OR REPLACE INTO issues (
                    key, project, summary, description, issue_type, status, priority,
                    assignee, reporter, created, updated, resolved, resolution,
                    labels, components, sprint_ids, story_points, raw_data, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                key,
                issue_data.get('fields', {}).get('project', {}).get('key'),
                fields.get('summary'),
                fields.get('description'),
                fields.get('issuetype', {}).get('name'),
                fields.get('status', {}).get('name'),
                fields.get('priority', {}).get('name') if fields.get('priority') else None,
                fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
                fields.get('reporter', {}).get('displayName') if fields.get('reporter') else None,
                fields.get('created'),
                fields.get('updated'),
                fields.get('resolutiondate'),
                fields.get('resolution', {}).get('name') if fields.get('resolution') else None,
                json.dumps(fields.get('labels', [])),
                json.dumps([c.get('name') for c in fields.get('components', [])]),
                json.dumps(sprint_ids),
                fields.get('customfield_10016'),  # Story points field
                json.dumps(issue_data),
                datetime.now().isoformat()
            ))

    def upsert_sprint(self, sprint_data: Dict):
        """
        Insert or update a sprint

        Args:
            sprint_data: Sprint data dictionary from JIRA
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sprints (
                    id, name, board_id, board_name, state, start_date, end_date,
                    complete_date, goal, raw_data, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sprint_data.get('id'),
                sprint_data.get('name'),
                sprint_data.get('originBoardId'),
                sprint_data.get('originBoardName', ''),
                sprint_data.get('state'),
                sprint_data.get('startDate'),
                sprint_data.get('endDate'),
                sprint_data.get('completeDate'),
                sprint_data.get('goal'),
                json.dumps(sprint_data),
                datetime.now().isoformat()
            ))

    def upsert_board(self, board_data: Dict):
        """
        Insert or update a board

        Args:
            board_data: Board data dictionary from JIRA
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            location = board_data.get('location', {})
            cursor.execute("""
                INSERT OR REPLACE INTO boards (
                    id, name, type, location_type, location_name, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                board_data.get('id'),
                board_data.get('name'),
                board_data.get('type'),
                location.get('projectKeyOrId'),
                location.get('displayName'),
                datetime.now().isoformat()
            ))

    def insert_changelog_entry(self, issue_key: str, changelog_item: Dict):
        """
        Insert changelog entry for an issue

        Args:
            issue_key: JIRA issue key
            changelog_item: Changelog item from JIRA
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            for item in changelog_item.get('items', []):
                cursor.execute("""
                    INSERT INTO issue_changelog (
                        issue_key, created, author, field, from_value, to_value
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    issue_key,
                    changelog_item.get('created'),
                    changelog_item.get('author', {}).get('displayName'),
                    item.get('field'),
                    item.get('fromString'),
                    item.get('toString')
                ))

    def get_issues(self, project: str = None, status: str = None,
                   issue_type: str = None, limit: int = None) -> List[Dict]:
        """
        Get issues from database

        Args:
            project: Filter by project key
            status: Filter by status
            issue_type: Filter by issue type
            limit: Maximum number of results

        Returns:
            List of issue dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM issues WHERE 1=1"
            params = []

            if project:
                query += " AND project = ?"
                params.append(project)
            if status:
                query += " AND status = ?"
                params.append(status)
            if issue_type:
                query += " AND issue_type = ?"
                params.append(issue_type)

            query += " ORDER BY created DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Convert rows to dictionaries and parse JSON fields
            issues = []
            for row in rows:
                issue = dict(row)
                issue['labels'] = json.loads(issue['labels']) if issue['labels'] else []
                issue['components'] = json.loads(issue['components']) if issue['components'] else []
                issue['sprint_ids'] = json.loads(issue['sprint_ids']) if issue['sprint_ids'] else []
                issues.append(issue)

            return issues

    def get_sprints(self, board_id: int = None, state: str = None) -> List[Dict]:
        """
        Get sprints from database

        Args:
            board_id: Filter by board ID
            state: Filter by state (active, closed, future)

        Returns:
            List of sprint dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM sprints WHERE 1=1"
            params = []

            if board_id:
                query += " AND board_id = ?"
                params.append(board_id)
            if state:
                query += " AND state = ?"
                params.append(state)

            query += " ORDER BY start_date DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def get_issue_changelog(self, issue_key: str) -> List[Dict]:
        """
        Get changelog for an issue

        Args:
            issue_key: JIRA issue key

        Returns:
            List of changelog entries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM issue_changelog
                WHERE issue_key = ?
                ORDER BY created
            """, (issue_key,))

            return [dict(row) for row in cursor.fetchall()]

    def get_sync_history(self, limit: int = 10) -> List[Dict]:
        """
        Get sync history

        Args:
            limit: Maximum number of results

        Returns:
            List of sync metadata dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sync_metadata
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            syncs = []
            for row in rows:
                sync = dict(row)
                sync['projects'] = json.loads(sync['projects']) if sync['projects'] else []
                syncs.append(sync)

            return syncs

    def get_last_sync(self) -> Optional[Dict]:
        """
        Get last successful sync

        Returns:
            Last sync metadata or None
        """
        syncs = self.get_sync_history(limit=1)
        return syncs[0] if syncs else None

    def get_stats(self) -> Dict:
        """
        Get database statistics

        Returns:
            Dictionary with database stats
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM issues")
            issues_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM sprints")
            sprints_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM boards")
            boards_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(DISTINCT project) as count FROM issues")
            projects_count = cursor.fetchone()['count']

            last_sync = self.get_last_sync()

            return {
                'issues_count': issues_count,
                'sprints_count': sprints_count,
                'boards_count': boards_count,
                'projects_count': projects_count,
                'last_sync': last_sync
            }

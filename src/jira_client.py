"""
JIRA API Client for Platform Engineering KPI Dashboard
Handles authentication, API calls, and data retrieval from JIRA
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth
import json
from functools import lru_cache


class JiraClient:
    """Client for interacting with JIRA REST API"""

    def __init__(self, jira_url: str, email: str, api_token: str):
        """
        Initialize JIRA client

        Args:
            jira_url: Base URL of JIRA instance
            email: User email for authentication
            api_token: JIRA API token
        """
        self.jira_url = jira_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger(__name__)

    def _make_request(self, endpoint: str, method: str = "GET", params: Dict = None, data: Dict = None, timeout: int = 30) -> Dict:
        """
        Make HTTP request to JIRA API

        Args:
            endpoint: API endpoint (e.g., '/rest/api/3/search')
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data
            timeout: Request timeout in seconds (default: 30)

        Returns:
            JSON response as dictionary
        """
        url = f"{self.jira_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=data,
                auth=self.auth,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"JIRA API request failed: {e}")
            raise

    def search_issues(self, jql: str, fields: List[str] = None, max_results: int = 1000) -> List[Dict]:
        """
        Search JIRA issues using JQL

        Args:
            jql: JQL query string
            fields: List of fields to return (None = all fields)
            max_results: Maximum number of results to return

        Returns:
            List of issue dictionaries
        """
        all_issues = []
        start_at = 0
        batch_size = 100  # JIRA API pagination limit

        if fields is None:
            fields = ["*all"]

        while start_at < max_results:
            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": min(batch_size, max_results - start_at),
                "fields": ",".join(fields)
            }

            self.logger.debug(f"Searching JIRA with JQL: {jql} (startAt: {start_at})")
            result = self._make_request("/rest/api/3/search", params=params)

            issues = result.get("issues", [])
            all_issues.extend(issues)

            total = result.get("total", 0)
            if start_at + batch_size >= total:
                break

            start_at += batch_size

        self.logger.info(f"Retrieved {len(all_issues)} issues from JIRA")
        return all_issues

    def get_sprints(self, board_id: int) -> List[Dict]:
        """
        Get sprints for a board

        Args:
            board_id: JIRA board ID

        Returns:
            List of sprint dictionaries
        """
        endpoint = f"/rest/agile/1.0/board/{board_id}/sprint"
        result = self._make_request(endpoint)
        return result.get("values", [])

    def get_boards(self, project_key: str = None) -> List[Dict]:
        """
        Get all boards (optionally filtered by project)

        Args:
            project_key: Optional project key to filter boards

        Returns:
            List of board dictionaries
        """
        params = {}
        if project_key:
            params["projectKeyOrId"] = project_key

        endpoint = "/rest/agile/1.0/board"
        result = self._make_request(endpoint, params=params)
        return result.get("values", [])

    def get_issue_changelog(self, issue_key: str) -> List[Dict]:
        """
        Get changelog for an issue

        Args:
            issue_key: JIRA issue key (e.g., 'PLATFORM-123')

        Returns:
            List of changelog entries
        """
        endpoint = f"/rest/api/3/issue/{issue_key}/changelog"
        result = self._make_request(endpoint)
        return result.get("values", [])

    def test_connection(self) -> bool:
        """
        Test JIRA connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            result = self._make_request("/rest/api/3/myself")
            self.logger.info(f"Connected to JIRA as: {result.get('displayName')}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to JIRA: {e}")
            return False

    def get_project_info(self, project_key: str) -> Dict:
        """
        Get project information

        Args:
            project_key: JIRA project key

        Returns:
            Project information dictionary
        """
        endpoint = f"/rest/api/3/project/{project_key}"
        return self._make_request(endpoint)

    def get_statuses(self) -> List[Dict]:
        """
        Get all available statuses

        Returns:
            List of status dictionaries
        """
        endpoint = "/rest/api/3/status"
        return self._make_request(endpoint)

    def get_issue_count(self, jql: str) -> int:
        """
        Get count of issues matching JQL query

        Args:
            jql: JQL query string

        Returns:
            Number of matching issues
        """
        params = {
            "jql": jql,
            "maxResults": 0  # We only want the count
        }
        result = self._make_request("/rest/api/3/search", params=params)
        return result.get("total", 0)

    def get_sprint_issues(self, sprint_id: int, fields: List[str] = None) -> List[Dict]:
        """
        Get all issues in a specific sprint

        Args:
            sprint_id: Sprint ID
            fields: List of fields to return

        Returns:
            List of issue dictionaries
        """
        jql = f"sprint = {sprint_id}"
        return self.search_issues(jql, fields=fields)

    def get_closed_sprints(self, board_id: int, count: int = 3) -> List[Dict]:
        """
        Get recently closed sprints for a board

        Args:
            board_id: JIRA board ID
            count: Number of closed sprints to retrieve

        Returns:
            List of sprint dictionaries
        """
        endpoint = f"/rest/agile/1.0/board/{board_id}/sprint"
        params = {"state": "closed"}
        result = self._make_request(endpoint, params=params)

        sprints = result.get("values", [])
        # Sort by end date descending and take the most recent
        sprints.sort(key=lambda x: x.get("endDate", ""), reverse=True)
        return sprints[:count]

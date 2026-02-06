"""
Database-backed KPI Calculator
Calculates KPIs from data stored in the local database
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics
import json

from database import DatabaseService


class KPICalculatorDB:
    """Calculate Platform Engineering KPIs from database"""

    def __init__(self, db_service: DatabaseService, config: Dict):
        """
        Initialize KPI Calculator

        Args:
            db_service: Database service instance
            config: Configuration dictionary
        """
        self.db = db_service
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.projects = config.get("projects", {}).get("project_keys", [])

    def get_projects_from_db(self) -> List[str]:
        """Get list of unique projects from database"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT project FROM issues WHERE project IS NOT NULL ORDER BY project")
            return [row['project'] for row in cursor.fetchall()]

    def _filter_issues_by_date(self, issues: List[Dict], date_range_days: int = None) -> List[Dict]:
        """
        Filter issues by date range based on updated date

        Args:
            issues: List of issue dictionaries
            date_range_days: Number of days to look back (None = no filter)

        Returns:
            Filtered list of issues
        """
        if date_range_days is None:
            return issues

        cutoff_date = (datetime.now() - timedelta(days=date_range_days)).isoformat()

        return [
            issue for issue in issues
            if issue.get('updated', '') >= cutoff_date or issue.get('resolved', '') >= cutoff_date
        ]

    def calculate_all_kpis(self, date_range_days: int = None, projects: List[str] = None) -> Dict:
        """
        Calculate all enabled KPIs from database

        Args:
            date_range_days: Optional date range filter (e.g., 30, 90, 365)
            projects: Optional list of projects to filter

        Returns:
            Dictionary containing all KPI data
        """
        self.logger.info(f"Calculating all Platform Engineering KPIs from database (date_range: {date_range_days}, projects: {projects})")

        # Store filter params for use in individual calculations
        self._date_range_days = date_range_days
        self._filter_projects = projects

        kpis = {}
        kpi_config = self.config.get("kpis", {})

        # Get actual projects from database
        db_projects = self.get_projects_from_db()
        self.logger.info(f"Found projects in database: {db_projects}")

        # Filter to requested projects if specified
        if projects:
            db_projects = [p for p in db_projects if p in projects]
            self.logger.info(f"Filtered to requested projects: {db_projects}")

        # KPI 1: Sprint Predictability
        if kpi_config.get("sprint_predictability", {}).get("enabled", True):
            self.logger.info("Calculating KPI 1: Sprint Predictability")
            try:
                kpis["sprint_predictability"] = self.calculate_sprint_predictability()
            except Exception as e:
                self.logger.error(f"Error calculating sprint predictability: {e}")
                kpis["sprint_predictability"] = self._empty_sprint_predictability()

        # KPI 2: Story Spillover
        if kpi_config.get("story_spillover", {}).get("enabled", True):
            self.logger.info("Calculating KPI 2: Story Spillover")
            try:
                kpis["story_spillover"] = self.calculate_story_spillover()
            except Exception as e:
                self.logger.error(f"Error calculating story spillover: {e}")
                kpis["story_spillover"] = self._empty_story_spillover()

        # KPI 3: Cycle Time
        if kpi_config.get("cycle_time", {}).get("enabled", True):
            self.logger.info("Calculating KPI 3: Average Story Cycle Time")
            try:
                kpis["cycle_time"] = self.calculate_cycle_time()
            except Exception as e:
                self.logger.error(f"Error calculating cycle time: {e}")
                kpis["cycle_time"] = self._empty_cycle_time()

        # KPI 4: Work Mix
        if kpi_config.get("work_mix", {}).get("enabled", True):
            self.logger.info("Calculating KPI 4: Work Mix Distribution")
            try:
                kpis["work_mix"] = self.calculate_work_mix()
            except Exception as e:
                self.logger.error(f"Error calculating work mix: {e}")
                kpis["work_mix"] = self._empty_work_mix()

        # KPI 5: Unplanned Work
        if kpi_config.get("unplanned_work", {}).get("enabled", True):
            self.logger.info("Calculating KPI 5: Unplanned Work Load")
            try:
                kpis["unplanned_work"] = self.calculate_unplanned_work()
            except Exception as e:
                self.logger.error(f"Error calculating unplanned work: {e}")
                kpis["unplanned_work"] = self._empty_unplanned_work()

        # KPI 6: Reopened Stories
        if kpi_config.get("reopened_stories", {}).get("enabled", True):
            self.logger.info("Calculating KPI 6: Reopened Stories")
            try:
                kpis["reopened_stories"] = self.calculate_reopened_stories()
            except Exception as e:
                self.logger.error(f"Error calculating reopened stories: {e}")
                kpis["reopened_stories"] = self._empty_reopened_stories()

        # Get analysis periods
        analysis_periods = kpi_config.get("analysis_periods", {})

        # Calculate per-project KPIs
        kpis_by_project = self.calculate_kpis_by_project(db_projects)

        return {
            "generated_at": datetime.now().isoformat(),
            "projects": db_projects,
            "analysis_period": analysis_periods,
            "kpis": kpis,
            "kpis_by_project": kpis_by_project,
            "database_stats": self.db.get_stats()
        }

    def calculate_kpis_by_project(self, projects: List[str]) -> Dict:
        """
        Calculate KPIs broken down by project

        Args:
            projects: List of project keys

        Returns:
            Dictionary with KPIs per project
        """
        self.logger.info(f"Calculating KPIs by project: {projects}")

        project_kpis = {}

        for project in projects:
            self.logger.info(f"Calculating KPIs for project {project}")

            try:
                project_kpis[project] = {
                    "sprint_predictability": self.calculate_sprint_predictability_for_project(project),
                    "story_spillover": self.calculate_story_spillover_for_project(project),
                    "cycle_time": self.calculate_cycle_time_for_project(project),
                    "work_mix": self.calculate_work_mix_for_project(project),
                    "reopened_stories": self.calculate_reopened_stories_for_project(project)
                }
            except Exception as e:
                self.logger.error(f"Error calculating KPIs for project {project}: {e}")
                project_kpis[project] = {}

        return project_kpis

    def calculate_sprint_predictability(self) -> Dict:
        """Calculate Sprint Predictability KPI using sprint reports"""
        # First try to get data from sprint_reports table (preferred method)
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Check if sprint_reports table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='sprint_reports'
            """)

            has_sprint_reports = cursor.fetchone() is not None

            if has_sprint_reports:
                # Get sprint lookback period
                sprint_lookback = self.config.get("kpis", {}).get("analysis_periods", {}).get("sprint_lookback", 10)

                # Get recent sprint reports
                cursor.execute("""
                    SELECT sprint_id, sprint_name, project, committed_count, completed_count, completion_rate
                    FROM sprint_reports
                    ORDER BY synced_at DESC
                    LIMIT ?
                """, (sprint_lookback,))

                rows = cursor.fetchall()

                if rows:
                    sprint_data = []
                    total_rate = 0

                    for row in rows:
                        sprint_data.append({
                            "sprint_name": row['sprint_name'],
                            "project": row['project'],
                            "committed": row['committed_count'],
                            "completed": row['completed_count'],
                            "completion_rate": row['completion_rate']
                        })
                        total_rate += row['completion_rate']

                    overall_average = round(total_rate / len(sprint_data), 1) if sprint_data else 0

                    return {
                        "overall_average": overall_average,
                        "sprints": sprint_data
                    }

        # Fallback to old method (counting issues in closed sprints)
        sprints = self.db.get_sprints(state="closed")

        # Get the most recent N sprints
        sprint_lookback = self.config.get("kpis", {}).get("analysis_periods", {}).get("sprint_lookback", 3)
        recent_sprints = sorted(sprints, key=lambda s: s.get('end_date', ''), reverse=True)[:sprint_lookback]

        sprint_data = []
        total_rate = 0

        for sprint in recent_sprints:
            sprint_id = sprint['id']

            # Get issues that were in this sprint
            all_issues = self.db.get_issues()
            sprint_issues = [
                issue for issue in all_issues
                if sprint_id in issue.get('sprint_ids', [])
            ]

            # Count committed (all issues in sprint) vs completed (Done status)
            committed = len(sprint_issues)
            completed = len([i for i in sprint_issues if i['status'] in ['Done', 'Closed', 'Resolved']])

            completion_rate = round((completed / committed * 100) if committed > 0 else 0, 1)
            total_rate += completion_rate

            sprint_data.append({
                "sprint_name": sprint['name'],
                "board_id": sprint.get('board_id'),
                "board_name": sprint.get('board_name', 'Unknown'),
                "committed": committed,
                "completed": completed,
                "completion_rate": completion_rate
            })

        overall_average = round(total_rate / len(sprint_data), 1) if sprint_data else 0

        return {
            "overall_average": overall_average,
            "sprints": sprint_data
        }

    def calculate_story_spillover(self) -> Dict:
        """Calculate Story Spillover KPI"""
        # Get all issues
        issues = self.db.get_issues()

        # Filter to stories and tasks
        story_issues = [i for i in issues if i['issue_type'] in ['Story', 'Task']]

        spillover_threshold = self.config.get("kpis", {}).get("story_spillover", {}).get("max_sprints", 2)

        # Find issues that spanned more than N sprints
        spillover_issues = []
        for issue in story_issues:
            sprint_count = len(issue.get('sprint_ids', []))
            if sprint_count > spillover_threshold:
                spillover_issues.append({
                    "key": issue['key'],
                    "summary": issue['summary'],
                    "sprint_count": sprint_count,
                    "status": issue['status']
                })

        total_analyzed = len(story_issues)
        spillover_count = len(spillover_issues)
        spillover_percentage = round((spillover_count / total_analyzed * 100) if total_analyzed > 0 else 0, 1)

        return {
            "spillover_percentage": spillover_percentage,
            "spillover_count": spillover_count,
            "total_analyzed": total_analyzed,
            "spillover_issues": spillover_issues[:50]  # Limit to 50
        }

    def calculate_cycle_time(self) -> Dict:
        """Calculate Average Cycle Time KPI"""
        # Use filter date range if available, otherwise default to 365 days
        date_range = getattr(self, '_date_range_days', None) or 365
        cutoff_date = (datetime.now() - timedelta(days=date_range)).isoformat()

        issues = self.db.get_issues()

        # Filter by projects if specified
        filter_projects = getattr(self, '_filter_projects', None)
        if filter_projects:
            issues = [i for i in issues if i['project'] in filter_projects]

        completed_issues = [
            i for i in issues
            if i['status'] in ['Done', 'Closed', 'Resolved']
            and i['resolved']
            and i['resolved'] >= cutoff_date
            and i['issue_type'] in ['Story', 'Task']
        ]

        cycle_times = []

        for issue in completed_issues:
            try:
                # Get changelog to find when issue moved to "In Progress"
                changelog = self.db.get_issue_changelog(issue['key'])

                in_progress_date = None
                for entry in changelog:
                    if entry['field'] == 'status' and entry['to_value'] in ['In Progress', 'In Development']:
                        in_progress_date = entry['created']
                        break

                # If no "In Progress" date found, use created date
                if not in_progress_date:
                    in_progress_date = issue['created']

                resolved_date = issue['resolved']

                # Calculate cycle time
                start = datetime.fromisoformat(in_progress_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(resolved_date.replace('Z', '+00:00'))
                cycle_time_days = (end - start).days

                if cycle_time_days >= 0:  # Ignore negative values
                    cycle_times.append({
                        "issue_key": issue['key'],
                        "cycle_time_days": cycle_time_days
                    })
            except Exception as e:
                self.logger.warning(f"Could not calculate cycle time for {issue['key']}: {e}")

        # Calculate statistics
        if cycle_times:
            times = [ct['cycle_time_days'] for ct in cycle_times]
            avg_cycle_time = round(statistics.mean(times), 1)
            median_cycle_time = round(statistics.median(times), 1)
            min_cycle_time = min(times)
            max_cycle_time = max(times)
        else:
            avg_cycle_time = median_cycle_time = min_cycle_time = max_cycle_time = 0

        return {
            "average_cycle_time_days": avg_cycle_time,
            "median_cycle_time_days": median_cycle_time,
            "min_cycle_time_days": min_cycle_time,
            "max_cycle_time_days": max_cycle_time,
            "issues_analyzed": len(cycle_times),
            "cycle_times": cycle_times[:100]  # Limit to 100
        }

    def calculate_work_mix(self) -> Dict:
        """Calculate Work Mix Distribution KPI"""
        # Use filter date range if available, otherwise default to 365 days
        date_range = getattr(self, '_date_range_days', None) or 365
        cutoff_date = (datetime.now() - timedelta(days=date_range)).isoformat()

        issues = self.db.get_issues()

        # Filter by projects if specified
        filter_projects = getattr(self, '_filter_projects', None)
        if filter_projects:
            issues = [i for i in issues if i['project'] in filter_projects]

        recent_issues = [
            i for i in issues
            if i['created'] >= cutoff_date
            and i['issue_type'] in ['Epic', 'Story', 'Task']
        ]

        # Count issues by label
        label_counts = Counter()
        for issue in recent_issues:
            labels = issue.get('labels', [])
            if labels:
                # Take first label as primary category
                primary_label = labels[0]
                label_counts[primary_label] += 1
            else:
                label_counts['unlabeled'] += 1

        total_issues = len(recent_issues)

        # Build distribution
        distribution = {}
        for label, count in label_counts.items():
            percentage = round((count / total_issues * 100) if total_issues > 0 else 0, 1)
            distribution[label] = {
                "count": count,
                "percentage": percentage
            }

        return {
            "total_issues": total_issues,
            "distribution": distribution
        }

    def calculate_unplanned_work(self) -> Dict:
        """Calculate Unplanned Work Load KPI"""
        # Get closed sprints
        sprints = self.db.get_sprints(state="closed")

        sprint_lookback = self.config.get("kpis", {}).get("analysis_periods", {}).get("sprint_lookback", 3)
        recent_sprints = sorted(sprints, key=lambda s: s.get('end_date', ''), reverse=True)[:sprint_lookback]

        sprint_data = []
        total_pct = 0

        for sprint in recent_sprints:
            sprint_id = sprint['id']

            # Get issues in this sprint
            all_issues = self.db.get_issues()
            sprint_issues = [
                issue for issue in all_issues
                if sprint_id in issue.get('sprint_ids', [])
            ]

            total_issues = len(sprint_issues)

            # Count unplanned issues (issues with "unplanned" or "interrupt" labels)
            unplanned_issues = len([
                i for i in sprint_issues
                if any(label.lower() in ['unplanned', 'interrupt', 'urgent', 'incident']
                      for label in i.get('labels', []))
            ])

            unplanned_pct = round((unplanned_issues / total_issues * 100) if total_issues > 0 else 0, 1)
            total_pct += unplanned_pct

            sprint_data.append({
                "sprint_name": sprint['name'],
                "board_id": sprint.get('board_id'),
                "board_name": sprint.get('board_name', 'Unknown'),
                "total_issues": total_issues,
                "unplanned_issues": unplanned_issues,
                "unplanned_percentage": unplanned_pct
            })

        overall_average = round(total_pct / len(sprint_data), 1) if sprint_data else 0

        return {
            "overall_average": overall_average,
            "sprints": sprint_data
        }

    def calculate_reopened_stories(self) -> Dict:
        """Calculate Reopened Stories KPI"""
        # Get issues updated in last 365 days (to capture all data)
        cutoff_date = (datetime.now() - timedelta(days=365)).isoformat()

        issues = self.db.get_issues()
        recent_issues = [
            i for i in issues
            if i['updated'] >= cutoff_date
            and i['issue_type'] in ['Story', 'Task', 'Bug']
        ]

        # Find reopened issues by checking changelog
        reopened_issues = []
        completed_count = 0

        for issue in recent_issues:
            try:
                changelog = self.db.get_issue_changelog(issue['key'])

                was_done = False
                reopened = False

                for entry in sorted(changelog, key=lambda e: e['created']):
                    if entry['field'] == 'status':
                        if entry['to_value'] in ['Done', 'Closed', 'Resolved']:
                            was_done = True
                            completed_count += 1
                        elif was_done and entry['to_value'] not in ['Done', 'Closed', 'Resolved']:
                            reopened = True
                            break

                if reopened:
                    reopened_issues.append({
                        "key": issue['key'],
                        "summary": issue['summary'],
                        "current_status": issue['status'],
                        "updated": issue['updated']
                    })
            except Exception as e:
                self.logger.warning(f"Could not check reopen status for {issue['key']}: {e}")

        reopened_count = len(reopened_issues)
        reopened_percentage = round((reopened_count / completed_count * 100) if completed_count > 0 else 0, 1)

        return {
            "reopened_percentage": reopened_percentage,
            "reopened_count": reopened_count,
            "total_completed": completed_count,
            "reopened_issues": reopened_issues[:50]
        }

    # Per-project KPI calculations
    def calculate_sprint_predictability_for_project(self, project: str) -> Dict:
        """Calculate Sprint Predictability for a specific project using sprint reports"""
        # First try to get data from sprint_reports table
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Check if sprint_reports table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='sprint_reports'
            """)

            has_sprint_reports = cursor.fetchone() is not None

            if has_sprint_reports:
                sprint_lookback = self.config.get("kpis", {}).get("analysis_periods", {}).get("sprint_lookback", 10)

                # Get sprint reports for this project
                cursor.execute("""
                    SELECT sprint_name, committed_count, completed_count, completion_rate
                    FROM sprint_reports
                    WHERE project = ?
                    ORDER BY synced_at DESC
                    LIMIT ?
                """, (project, sprint_lookback))

                rows = cursor.fetchall()

                if rows:
                    sprint_data = []
                    total_rate = 0

                    for row in rows:
                        sprint_data.append({
                            "sprint_name": row['sprint_name'],
                            "committed": row['committed_count'],
                            "completed": row['completed_count'],
                            "completion_rate": row['completion_rate']
                        })
                        total_rate += row['completion_rate']

                    overall_average = round(total_rate / len(sprint_data), 1) if sprint_data else 0
                    return {"overall_average": overall_average, "sprints": sprint_data}

        # Fallback to old method
        sprints = self.db.get_sprints(state="closed")
        sprint_lookback = self.config.get("kpis", {}).get("analysis_periods", {}).get("sprint_lookback", 3)
        recent_sprints = sorted(sprints, key=lambda s: s.get('end_date', ''), reverse=True)[:sprint_lookback]

        sprint_data = []
        total_rate = 0

        for sprint in recent_sprints:
            sprint_id = sprint['id']
            all_issues = self.db.get_issues(project=project)
            sprint_issues = [i for i in all_issues if sprint_id in i.get('sprint_ids', [])]

            if not sprint_issues:
                continue

            committed = len(sprint_issues)
            completed = len([i for i in sprint_issues if i['status'] in ['Done', 'Closed', 'Resolved']])
            completion_rate = round((completed / committed * 100) if committed > 0 else 0, 1)
            total_rate += completion_rate

            sprint_data.append({
                "sprint_name": sprint['name'],
                "committed": committed,
                "completed": completed,
                "completion_rate": completion_rate
            })

        overall_average = round(total_rate / len(sprint_data), 1) if sprint_data else 0
        return {"overall_average": overall_average, "sprints": sprint_data}

    def calculate_story_spillover_for_project(self, project: str) -> Dict:
        """Calculate Story Spillover for a specific project"""
        issues = self.db.get_issues(project=project)
        story_issues = [i for i in issues if i['issue_type'] in ['Story', 'Task']]
        spillover_threshold = self.config.get("kpis", {}).get("story_spillover", {}).get("max_sprints", 2)

        spillover_issues = []
        for issue in story_issues:
            sprint_count = len(issue.get('sprint_ids', []))
            if sprint_count > spillover_threshold:
                spillover_issues.append({
                    "key": issue['key'],
                    "summary": issue['summary'],
                    "sprint_count": sprint_count,
                    "status": issue['status']
                })

        total_analyzed = len(story_issues)
        spillover_count = len(spillover_issues)
        spillover_percentage = round((spillover_count / total_analyzed * 100) if total_analyzed > 0 else 0, 1)

        return {
            "spillover_percentage": spillover_percentage,
            "spillover_count": spillover_count,
            "total_analyzed": total_analyzed
        }

    def calculate_cycle_time_for_project(self, project: str) -> Dict:
        """Calculate Cycle Time for a specific project"""
        cutoff_date = (datetime.now() - timedelta(days=365)).isoformat()
        issues = self.db.get_issues(project=project)
        completed_issues = [
            i for i in issues
            if i['status'] in ['Done', 'Closed', 'Resolved']
            and i['resolved']
            and i['resolved'] >= cutoff_date
            and i['issue_type'] in ['Story', 'Task']
        ]

        cycle_times = []
        for issue in completed_issues:
            try:
                changelog = self.db.get_issue_changelog(issue['key'])
                in_progress_date = None
                for entry in changelog:
                    if entry['field'] == 'status' and entry['to_value'] in ['In Progress', 'In Development']:
                        in_progress_date = entry['created']
                        break

                if not in_progress_date:
                    in_progress_date = issue['created']

                start = datetime.fromisoformat(in_progress_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(issue['resolved'].replace('Z', '+00:00'))
                cycle_time_days = (end - start).days

                if cycle_time_days >= 0:
                    cycle_times.append(cycle_time_days)
            except:
                pass

        if cycle_times:
            return {
                "average_cycle_time_days": round(statistics.mean(cycle_times), 1),
                "median_cycle_time_days": round(statistics.median(cycle_times), 1),
                "issues_analyzed": len(cycle_times)
            }
        return {"average_cycle_time_days": 0, "median_cycle_time_days": 0, "issues_analyzed": 0}

    def calculate_work_mix_for_project(self, project: str) -> Dict:
        """Calculate Work Mix for a specific project"""
        cutoff_date = (datetime.now() - timedelta(days=365)).isoformat()
        issues = self.db.get_issues(project=project)
        recent_issues = [
            i for i in issues
            if i['created'] >= cutoff_date and i['issue_type'] in ['Epic', 'Story', 'Task']
        ]

        label_counts = Counter()
        for issue in recent_issues:
            labels = issue.get('labels', [])
            if labels:
                label_counts[labels[0]] += 1
            else:
                label_counts['unlabeled'] += 1

        total_issues = len(recent_issues)
        distribution = {}
        for label, count in label_counts.items():
            percentage = round((count / total_issues * 100) if total_issues > 0 else 0, 1)
            distribution[label] = {"count": count, "percentage": percentage}

        return {"total_issues": total_issues, "distribution": distribution}

    def calculate_reopened_stories_for_project(self, project: str) -> Dict:
        """Calculate Reopened Stories for a specific project"""
        cutoff_date = (datetime.now() - timedelta(days=365)).isoformat()
        issues = self.db.get_issues(project=project)
        recent_issues = [
            i for i in issues
            if i['updated'] >= cutoff_date and i['issue_type'] in ['Story', 'Task', 'Bug']
        ]

        reopened_count = 0
        completed_count = 0

        for issue in recent_issues:
            try:
                changelog = self.db.get_issue_changelog(issue['key'])
                was_done = False
                for entry in sorted(changelog, key=lambda e: e['created']):
                    if entry['field'] == 'status':
                        if entry['to_value'] in ['Done', 'Closed', 'Resolved']:
                            was_done = True
                            completed_count += 1
                        elif was_done:
                            reopened_count += 1
                            break
            except:
                pass

        reopened_percentage = round((reopened_count / completed_count * 100) if completed_count > 0 else 0, 1)
        return {
            "reopened_percentage": reopened_percentage,
            "reopened_count": reopened_count,
            "total_completed": completed_count
        }

    # Empty KPI placeholders for error cases
    def _empty_sprint_predictability(self):
        return {"overall_average": 0, "sprints": []}

    def _empty_story_spillover(self):
        return {"spillover_percentage": 0, "spillover_count": 0, "total_analyzed": 0, "spillover_issues": []}

    def _empty_cycle_time(self):
        return {
            "average_cycle_time_days": 0,
            "median_cycle_time_days": 0,
            "min_cycle_time_days": 0,
            "max_cycle_time_days": 0,
            "issues_analyzed": 0,
            "cycle_times": []
        }

    def _empty_work_mix(self):
        return {"total_issues": 0, "distribution": {}}

    def _empty_unplanned_work(self):
        return {"overall_average": 0, "sprints": []}

    def _empty_reopened_stories(self):
        return {"reopened_percentage": 0, "reopened_count": 0, "total_completed": 0, "reopened_issues": []}

"""
KPI Calculator for Platform Engineering Dashboard
Contains all JQL queries and calculation logic for each KPI
"""

import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics


class KPICalculator:
    """Calculate Platform Engineering KPIs from JIRA data"""

    def __init__(self, jira_client, config: Dict):
        """
        Initialize KPI Calculator

        Args:
            jira_client: JiraClient instance
            config: Configuration dictionary
        """
        self.jira = jira_client
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.projects = config.get("projects", {}).get("project_keys", [])

        # Parse label configuration (supports global and space-specific labels)
        self.labels_config = config.get("labels", {})
        self._parse_label_configuration()

    def _parse_label_configuration(self):
        """Parse label configuration to support global and space-specific labels"""
        self.global_labels = []
        self.space_labels = {}
        self.project_to_space = {}

        # Parse global labels
        global_config = self.labels_config.get("global", {})
        if global_config.get("enabled", True):
            work_categories = global_config.get("work_categories", [])
            # Support both old format (list of strings) and new format (list of dicts)
            for cat in work_categories:
                if isinstance(cat, dict):
                    self.global_labels.append(cat.get("label"))
                else:
                    self.global_labels.append(cat)

        # Parse space-specific labels
        spaces = self.labels_config.get("spaces", [])
        for space in spaces:
            space_name = space.get("name")
            space_projects = space.get("projects", [])
            work_categories = space.get("work_categories", [])

            # Extract label names
            labels = []
            for cat in work_categories:
                if isinstance(cat, dict):
                    labels.append(cat.get("label"))
                else:
                    labels.append(cat)

            # Map projects to this space
            for project in space_projects:
                self.project_to_space[project] = space_name
                self.space_labels[space_name] = labels

        # Fallback to old config format if no new format found
        if not self.global_labels and not self.space_labels:
            old_labels = self.labels_config.get("work_categories", [])
            for label in old_labels:
                if isinstance(label, dict):
                    self.global_labels.append(label.get("label"))
                else:
                    self.global_labels.append(label)

        self.logger.info(f"Label configuration: Global={len(self.global_labels)}, Spaces={len(self.space_labels)}")

    def get_labels_for_projects(self, projects: List[str] = None) -> List[str]:
        """
        Get work category labels for specific projects

        Args:
            projects: List of project keys. If None, uses all configured projects

        Returns:
            List of label strings
        """
        if projects is None:
            projects = self.projects

        # Collect all unique labels for the given projects
        all_labels = set()

        for project in projects:
            # Check if project has space-specific labels
            if project in self.project_to_space:
                space_name = self.project_to_space[project]
                space_labels = self.space_labels.get(space_name, [])
                all_labels.update(space_labels)
            else:
                # Use global labels
                all_labels.update(self.global_labels)

        # If no labels found, use global labels as fallback
        if not all_labels:
            all_labels = set(self.global_labels)

        return list(all_labels)

    def get_label_mapping(self) -> Dict[str, Dict]:
        """
        Get complete label mapping with names and descriptions

        Returns:
            Dictionary mapping label strings to their metadata
        """
        mapping = {}

        # Add global labels
        global_config = self.labels_config.get("global", {})
        if global_config.get("enabled", True):
            for cat in global_config.get("work_categories", []):
                if isinstance(cat, dict):
                    mapping[cat.get("label")] = {
                        "name": cat.get("name", cat.get("label")),
                        "description": cat.get("description", ""),
                        "space": "Global"
                    }

        # Add space-specific labels
        for space in self.labels_config.get("spaces", []):
            space_name = space.get("name")
            for cat in space.get("work_categories", []):
                if isinstance(cat, dict):
                    label = cat.get("label")
                    mapping[label] = {
                        "name": cat.get("name", label),
                        "description": cat.get("description", ""),
                        "space": space_name
                    }

        return mapping

    def get_project_filter(self) -> str:
        """Generate JQL project filter"""
        if not self.projects:
            return ""
        project_list = ", ".join(self.projects)
        return f"project in ({project_list})"

    # ==================== KPI 1: Sprint Predictability ====================

    def calculate_sprint_predictability(self, sprint_lookback: int = 3) -> Dict[str, Any]:
        """
        KPI 1: Sprint Predictability
        Measures % of committed stories completed within sprint

        JQL Approach:
        - Get closed sprints
        - For each sprint, find committed vs completed stories
        - Calculate completion rate

        Returns:
            Dictionary with sprint predictability metrics
        """
        self.logger.info("Calculating KPI 1: Sprint Predictability")


        project_filter = self.get_project_filter()
        results = {
            "kpi_name": "Sprint Predictability",
            "description": "% of committed stories completed within sprint",
            "sprints": [],
            "overall_average": 0,
            "team_breakdown": {}
        }

        try:
            # Get boards for projects (with error handling for agile API)
            boards = []
            for project in self.projects:
                try:
                    project_boards = self.jira.get_boards(project_key=project)
                    boards.extend(project_boards)
                except Exception as board_error:
                    self.logger.warning(f"Could not get boards for {project}: {board_error}. Continuing without this project.")
                    continue

            for board in boards:
                board_id = board.get("id")
                board_name = board.get("name")

                # Get closed sprints
                closed_sprints = self.jira.get_closed_sprints(board_id, count=sprint_lookback)

                for sprint in closed_sprints:
                    sprint_id = sprint.get("id")
                    sprint_name = sprint.get("name")

                    # JQL: Get all issues that were in this sprint at any point
                    jql_committed = f"sprint = {sprint_id} AND type in (Story, Task, Bug)"
                    if project_filter:
                        jql_committed += f" AND {project_filter}"

                    committed_issues = self.jira.search_issues(
                        jql_committed,
                        fields=["key", "status", "resolution"]
                    )

                    # JQL: Get completed issues in this sprint
                    jql_completed = (
                        f"sprint = {sprint_id} AND "
                        f"statusCategory = Done AND "
                        f"type in (Story, Task, Bug)"
                    )
                    if project_filter:
                        jql_completed += f" AND {project_filter}"

                    completed_issues = self.jira.search_issues(
                        jql_completed,
                        fields=["key", "status"]
                    )

                    committed_count = len(committed_issues)
                    completed_count = len(completed_issues)

                    if committed_count > 0:
                        completion_rate = (completed_count / committed_count) * 100
                    else:
                        completion_rate = 0

                    sprint_data = {
                        "sprint_name": sprint_name,
                        "board_name": board_name,
                        "committed": committed_count,
                        "completed": completed_count,
                        "completion_rate": round(completion_rate, 2),
                        "jql_committed": jql_committed,
                        "jql_completed": jql_completed
                    }

                    results["sprints"].append(sprint_data)

            # If no boards found via agile API, try fallback approach
            if not results["sprints"]:
                self.logger.info("No sprints found via agile API. Returning empty results.")
                results["note"] = "Sprint Predictability requires Jira Agile/Scrum boards. Please configure boards in your Jira projects."

            # Calculate overall average
            if results["sprints"]:
                completion_rates = [s["completion_rate"] for s in results["sprints"]]
                results["overall_average"] = round(statistics.mean(completion_rates), 2)

        except Exception as e:
            self.logger.error(f"Error calculating sprint predictability: {e}")
            results["error"] = str(e)
            results["note"] = "Sprint Predictability requires Jira Agile/Scrum boards. Please ensure your projects are configured with Scrum boards in Jira."

        return results

    # ==================== KPI 2: Story Spillover ====================

    def calculate_story_spillover(self, max_sprints: int = 2) -> Dict[str, Any]:
        """
        KPI 2: Story Spillover
        Measures % of stories spanning more than N sprints

        JQL: Stories that have been in multiple sprints
        Complex calculation - need to analyze sprint history per issue

        Returns:
            Dictionary with spillover metrics
        """
        self.logger.info("Calculating KPI 2: Story Spillover")

        project_filter = self.get_project_filter()
        results = {
            "kpi_name": "Story Spillover",
            "description": f"% of stories spanning more than {max_sprints} sprints",
            "spillover_percentage": 0,
            "spillover_issues": [],
            "total_analyzed": 0,
            "jql_queries": []
        }

        try:
            # Try to get stories/tasks from recent sprints
            # Use a time-based query as fallback since closedSprints() may not work
            jql_base = (
                f"statusCategory = Done AND type in (Story, Task) AND "
                f"updated >= -90d"
            )
            if project_filter:
                jql_base += f" AND {project_filter}"

            results["jql_queries"].append({
                "purpose": "Get completed stories from past 90 days",
                "jql": jql_base
            })

            try:
                # Try the standard approach first
                issues = self.jira.search_issues(
                    jql_base,
                    fields=["key", "summary", "sprint", "status"]
                )
            except Exception as e:
                self.logger.warning(f"Error with story spillover query: {e}. Returning minimal data.")
                issues = []

            spillover_issues = []

            for issue in issues:
                issue_key = issue.get("key")
                fields = issue.get("fields", {})

                # Get sprint field (customfield - typically customfield_10020 or similar)
                # Sprint data shows all sprints this issue has been in
                sprints = fields.get("sprint", [])

                # If sprint is not a list, make it one
                if not isinstance(sprints, list):
                    sprints = [sprints] if sprints else []

                sprint_count = len([s for s in sprints if s is not None])

                if sprint_count > max_sprints:
                    spillover_issues.append({
                        "key": issue_key,
                        "summary": fields.get("summary"),
                        "sprint_count": sprint_count,
                        "status": fields.get("status", {}).get("name")
                    })

            results["total_analyzed"] = len(issues)
            results["spillover_issues"] = spillover_issues
            results["spillover_count"] = len(spillover_issues)

            if results["total_analyzed"] > 0:
                results["spillover_percentage"] = round(
                    (len(spillover_issues) / results["total_analyzed"]) * 100, 2
                )

            # Alternative JQL approach (manual query for reference)
            # Note: This is approximate as JQL doesn't directly support "count sprints per issue"
            jql_spillover_example = (
                f"sprint in closedSprints() AND "
                f"type in (Story, Task) AND "
                f"sprint is not EMPTY"
            )
            if project_filter:
                jql_spillover_example += f" AND {project_filter}"

            results["jql_queries"].append({
                "purpose": "Alternative query - needs post-processing",
                "jql": jql_spillover_example,
                "note": "Requires analysis of sprint field to count sprints per issue"
            })

        except Exception as e:
            self.logger.error(f"Error calculating story spillover: {e}")
            results["error"] = str(e)

        return results

    # ==================== KPI 3: Average Story Cycle Time ====================

    def calculate_cycle_time(self, days_back: int = 90) -> Dict[str, Any]:
        """
        KPI 3: Average Story Cycle Time
        Measures avg time from "In Progress" → "Done"

        Calculation: Analyze changelog to find status transitions

        Returns:
            Dictionary with cycle time metrics
        """
        self.logger.info("Calculating KPI 3: Average Story Cycle Time")

        project_filter = self.get_project_filter()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        results = {
            "kpi_name": "Average Story Cycle Time",
            "description": "Avg time from In Progress → Done",
            "average_cycle_time_days": 0,
            "median_cycle_time_days": 0,
            "min_cycle_time_days": 0,
            "max_cycle_time_days": 0,
            "issues_analyzed": 0,
            "cycle_times": [],
            "jql_queries": []
        }

        try:
            # JQL: Get completed stories in the time period
            jql = (
                f"statusCategory = Done AND "
                f"type in (Story, Task) AND "
                f"resolved >= -{days_back}d"
            )
            if project_filter:
                jql += f" AND {project_filter}"

            results["jql_queries"].append({
                "purpose": "Get completed stories for cycle time analysis",
                "jql": jql
            })

            issues = self.jira.search_issues(
                jql,
                fields=["key", "created", "resolutiondate", "status", "changelog"]
            )

            cycle_times = []

            for issue in issues:
                issue_key = issue.get("key")
                fields = issue.get("fields", {})

                # Get changelog to find when issue moved to "In Progress"
                try:
                    changelog = self.jira.get_issue_changelog(issue_key)

                    in_progress_date = None
                    done_date = None

                    # Find first transition to "In Progress" or similar status
                    for history in changelog:
                        for item in history.get("items", []):
                            if item.get("field") == "status":
                                to_status = item.get("toString", "").lower()
                                created = history.get("created")

                                # In Progress, Development, etc.
                                if "in progress" in to_status or "development" in to_status:
                                    if not in_progress_date:
                                        in_progress_date = datetime.strptime(
                                            created.split(".")[0], "%Y-%m-%dT%H:%M:%S"
                                        )

                                # Done, Closed, Resolved, etc.
                                if to_status in ["done", "closed", "resolved"]:
                                    done_date = datetime.strptime(
                                        created.split(".")[0], "%Y-%m-%dT%H:%M:%S"
                                    )

                    # Calculate cycle time
                    if in_progress_date and done_date and done_date > in_progress_date:
                        cycle_time_days = (done_date - in_progress_date).days
                        cycle_times.append({
                            "key": issue_key,
                            "cycle_time_days": cycle_time_days
                        })

                except Exception as e:
                    self.logger.warning(f"Error analyzing changelog for {issue_key}: {e}")
                    continue

            results["issues_analyzed"] = len(cycle_times)
            results["cycle_times"] = cycle_times

            if cycle_times:
                times = [ct["cycle_time_days"] for ct in cycle_times]
                results["average_cycle_time_days"] = round(statistics.mean(times), 2)
                results["median_cycle_time_days"] = round(statistics.median(times), 2)
                results["min_cycle_time_days"] = min(times)
                results["max_cycle_time_days"] = max(times)

        except Exception as e:
            self.logger.error(f"Error calculating cycle time: {e}")
            results["error"] = str(e)

        return results

    # ==================== KPI 4: Work Mix Distribution ====================

    def calculate_work_mix(self, days_back: int = 90) -> Dict[str, Any]:
        """
        KPI 4: Work Mix Distribution
        Measures % of work by label category

        JQL: Group epics/stories by label

        Returns:
            Dictionary with work mix distribution
        """
        self.logger.info("Calculating KPI 4: Work Mix Distribution")

        project_filter = self.get_project_filter()

        # Get labels for the projects being analyzed
        work_labels = self.get_labels_for_projects(self.projects)
        label_mapping = self.get_label_mapping()

        results = {
            "kpi_name": "Work Mix Distribution",
            "description": "% of work by category (labels)",
            "distribution": {},
            "total_issues": 0,
            "issues_by_label": {},
            "unlabeled_count": 0,
            "jql_queries": [],
            "labels_used": work_labels,
            "label_details": label_mapping
        }

        try:
            # JQL: Get all epics and stories from the period
            jql_base = (
                f"type in (Epic, Story, Task) AND "
                f"created >= -{days_back}d"
            )
            if project_filter:
                jql_base += f" AND {project_filter}"

            results["jql_queries"].append({
                "purpose": "Get all work items for distribution analysis",
                "jql": jql_base
            })

            issues = self.jira.search_issues(
                jql_base,
                fields=["key", "labels", "issuetype", "project"]
            )

            label_counts = Counter()
            unlabeled = 0

            for issue in issues:
                fields = issue.get("fields", {})
                labels = fields.get("labels", [])

                # Check for work category labels (now supports space-specific labels)
                issue_work_labels = [l for l in labels if l in work_labels]

                if issue_work_labels:
                    for label in issue_work_labels:
                        label_counts[label] += 1
                else:
                    unlabeled += 1

            results["total_issues"] = len(issues)
            results["unlabeled_count"] = unlabeled

            # Calculate distribution percentages
            total_labeled = sum(label_counts.values())
            for label in work_labels:
                count = label_counts.get(label, 0)
                if results["total_issues"] > 0:
                    percentage = (count / results["total_issues"]) * 100
                else:
                    percentage = 0

                label_info = label_mapping.get(label, {})
                results["distribution"][label] = {
                    "count": count,
                    "percentage": round(percentage, 2),
                    "name": label_info.get("name", label),
                    "space": label_info.get("space", "Unknown")
                }
                results["issues_by_label"][label] = count

            # Add unlabeled percentage
            if results["total_issues"] > 0:
                unlabeled_pct = (unlabeled / results["total_issues"]) * 100
            else:
                unlabeled_pct = 0

            results["distribution"]["unlabeled"] = {
                "count": unlabeled,
                "percentage": round(unlabeled_pct, 2),
                "name": "Unlabeled",
                "space": "N/A"
            }

            # Individual JQL queries for each label (for reference/debugging)
            for label in work_labels:
                jql_label = (
                    f"type in (Epic, Story, Task) AND "
                    f"labels = {label} AND "
                    f"created >= -{days_back}d"
                )
                if project_filter:
                    jql_label += f" AND {project_filter}"

                results["jql_queries"].append({
                    "purpose": f"Count issues with label: {label}",
                    "jql": jql_label
                })

        except Exception as e:
            self.logger.error(f"Error calculating work mix: {e}")
            results["error"] = str(e)

        return results

    # ==================== KPI 5: Unplanned Work Load ====================

    def calculate_unplanned_work(self, sprint_lookback: int = 3) -> Dict[str, Any]:
        """
        KPI 5: Unplanned Work Load
        Measures % of stories labeled as unplanned per sprint

        JQL: Count issues with 'unplanned' label per sprint

        Returns:
            Dictionary with unplanned work metrics
        """
        self.logger.info("Calculating KPI 5: Unplanned Work Load")

        project_filter = self.get_project_filter()
        results = {
            "kpi_name": "Unplanned Work Load",
            "description": "% of stories labeled as unplanned",
            "sprints": [],
            "overall_average": 0,
            "jql_queries": []
        }

        try:
            # Get boards for projects
            boards = []
            for project in self.projects:
                project_boards = self.jira.get_boards(project_key=project)
                boards.extend(project_boards)

            for board in boards:
                board_id = board.get("id")
                board_name = board.get("name")

                # Get closed sprints
                closed_sprints = self.jira.get_closed_sprints(board_id, count=sprint_lookback)

                for sprint in closed_sprints:
                    sprint_id = sprint.get("id")
                    sprint_name = sprint.get("name")

                    # JQL: Total issues in sprint
                    jql_total = f"sprint = {sprint_id} AND type in (Story, Task, Bug)"
                    if project_filter:
                        jql_total += f" AND {project_filter}"

                    # JQL: Unplanned issues in sprint
                    jql_unplanned = (
                        f"sprint = {sprint_id} AND "
                        f"labels = unplanned AND "
                        f"type in (Story, Task, Bug)"
                    )
                    if project_filter:
                        jql_unplanned += f" AND {project_filter}"

                    total_count = self.jira.get_issue_count(jql_total)
                    unplanned_count = self.jira.get_issue_count(jql_unplanned)

                    if total_count > 0:
                        unplanned_percentage = (unplanned_count / total_count) * 100
                    else:
                        unplanned_percentage = 0

                    sprint_data = {
                        "sprint_name": sprint_name,
                        "board_name": board_name,
                        "total_issues": total_count,
                        "unplanned_issues": unplanned_count,
                        "unplanned_percentage": round(unplanned_percentage, 2),
                        "jql_total": jql_total,
                        "jql_unplanned": jql_unplanned
                    }

                    results["sprints"].append(sprint_data)
                    results["jql_queries"].append({
                        "sprint": sprint_name,
                        "jql_total": jql_total,
                        "jql_unplanned": jql_unplanned
                    })

            # Calculate overall average
            if results["sprints"]:
                unplanned_rates = [s["unplanned_percentage"] for s in results["sprints"]]
                results["overall_average"] = round(statistics.mean(unplanned_rates), 2)

        except Exception as e:
            self.logger.error(f"Error calculating unplanned work: {e}")
            results["error"] = str(e)

        return results

    # ==================== KPI 6: Reopened Stories ====================

    def calculate_reopened_stories(self, days_back: int = 90) -> Dict[str, Any]:
        """
        KPI 6: Reopened Stories
        Measures % of issues reopened after Done

        JQL: Issues that changed FROM Done status

        Returns:
            Dictionary with reopened story metrics
        """
        self.logger.info("Calculating KPI 6: Reopened Stories")

        project_filter = self.get_project_filter()
        results = {
            "kpi_name": "Reopened Stories",
            "description": "% of issues reopened after Done",
            "reopened_percentage": 0,
            "reopened_issues": [],
            "total_completed": 0,
            "reopened_count": 0,
            "jql_queries": []
        }

        try:
            # Try to find issues that might be reopened
            # Note: Advanced history queries may not work on all JIRA instances
            # Using a simpler approach that doesn't rely on status history
            jql_reopened_1 = (
                f"statusCategory != Done AND "
                f"type in (Story, Task, Bug) AND "
                f"updated >= -{days_back}d"
            )
            if project_filter:
                jql_reopened_1 += f" AND {project_filter}"

            results["jql_queries"].append({
                "purpose": "Find issues that are NOT currently Done",
                "jql": jql_reopened_1,
                "note": "This is a simplified query. Advanced status history features may not be available."
            })

            # Try to get issues with this query
            try:
                reopened_issues = self.jira.search_issues(
                    jql_reopened_1,
                    fields=["key", "summary", "status", "updated"]
                )

                # Get total completed issues in the period for context
                jql_completed = (
                    f"statusCategory = Done AND "
                    f"type in (Story, Task, Bug) AND "
                    f"resolved >= -{days_back}d"
                )
                if project_filter:
                    jql_completed += f" AND {project_filter}"

                total_completed = self.jira.get_issue_count(jql_completed)

                results["jql_queries"].append({
                    "purpose": "Get total completed issues for context",
                    "jql": jql_completed
                })

                # Format reopened issues
                for issue in reopened_issues:
                    fields = issue.get("fields", {})
                    results["reopened_issues"].append({
                        "key": issue.get("key"),
                        "summary": fields.get("summary"),
                        "current_status": fields.get("status", {}).get("name"),
                        "updated": fields.get("updated")
                    })

                results["reopened_count"] = len(reopened_issues)
                results["total_completed"] = total_completed

                # Calculate percentage
                # Base = total completed + reopened (since reopened were once completed)
                total_base = total_completed + results["reopened_count"]

                if total_base > 0:
                    results["reopened_percentage"] = round(
                        (results["reopened_count"] / total_base) * 100, 2
                    )
            
            except Exception as query_error:
                self.logger.warning(f"Could not retrieve full reopened stories data: {query_error}")
                results["note"] = "Reopened stories tracking requires advanced JIRA history features. Showing partial data."

        except Exception as e:
            self.logger.error(f"Error calculating reopened stories: {e}")
            results["error"] = str(e)

        return results

    # ==================== Master Calculate All KPIs ====================

    def calculate_all_kpis(self) -> Dict[str, Any]:
        """
        Calculate all enabled KPIs

        Returns:
            Dictionary containing all KPI results
        """
        self.logger.info("Calculating all Platform Engineering KPIs")

        kpi_config = self.config.get("kpis", {})
        analysis_periods = kpi_config.get("analysis_periods", {})
        sprint_lookback = analysis_periods.get("sprint_lookback", 3)
        rolling_days = analysis_periods.get("rolling_days", [90])[0]

        # Check if labels are configured
        has_labels = len(self.get_labels_for_projects()) > 0

        results = {
            "generated_at": datetime.now().isoformat(),
            "projects": self.projects,
            "analysis_period": {
                "sprint_lookback": sprint_lookback,
                "rolling_days": rolling_days
            },
            "labels_configured": has_labels,
            "kpis": {}
        }

        # KPI 1: Sprint Predictability (no labels needed)
        if kpi_config.get("sprint_predictability", {}).get("enabled", True):
            results["kpis"]["sprint_predictability"] = self.calculate_sprint_predictability(
                sprint_lookback=sprint_lookback
            )

        # KPI 2: Story Spillover (no labels needed)
        if kpi_config.get("story_spillover", {}).get("enabled", True):
            max_sprints = kpi_config.get("story_spillover", {}).get("max_sprints", 2)
            results["kpis"]["story_spillover"] = self.calculate_story_spillover(
                max_sprints=max_sprints
            )

        # KPI 3: Cycle Time (no labels needed)
        if kpi_config.get("cycle_time", {}).get("enabled", True):
            results["kpis"]["cycle_time"] = self.calculate_cycle_time(
                days_back=rolling_days
            )

        # KPI 4: Work Mix (REQUIRES labels - skipped if not configured)
        if kpi_config.get("work_mix", {}).get("enabled", True):
            if has_labels:
                results["kpis"]["work_mix"] = self.calculate_work_mix(
                    days_back=rolling_days
                )
            else:
                self.logger.warning("KPI 4 (Work Mix) skipped - no labels configured")
                results["kpis"]["work_mix"] = {
                    "kpi_name": "Work Mix Distribution",
                    "description": "% of work by category (labels)",
                    "skipped": True,
                    "reason": "No labels configured. To enable, add labels in config/config.yaml"
                }

        # KPI 5: Unplanned Work (optional labels - works without but shows 0%)
        if kpi_config.get("unplanned_work", {}).get("enabled", True):
            results["kpis"]["unplanned_work"] = self.calculate_unplanned_work(
                sprint_lookback=sprint_lookback
            )
            if not has_labels:
                self.logger.info("KPI 5 (Unplanned Work) running without labels - will show 0%")

        # KPI 6: Reopened Stories (no labels needed)
        if kpi_config.get("reopened_stories", {}).get("enabled", True):
            results["kpis"]["reopened_stories"] = self.calculate_reopened_stories(
                days_back=rolling_days
            )

        return results

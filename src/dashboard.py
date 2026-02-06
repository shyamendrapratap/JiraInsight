"""
Dashboard Visualization for Platform Engineering KPIs
Web-based dashboard using Plotly Dash
"""

import logging
from typing import Dict, Any
from copy import deepcopy
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime
import json


class KPIDashboard:
    """Interactive dashboard for Platform Engineering KPIs"""

    def __init__(self, config: Dict, kpi_data: Dict = None, db=None, calculator=None):
        """
        Initialize dashboard

        Args:
            config: Configuration dictionary
            kpi_data: Pre-calculated KPI data (optional)
            db: Database service (for filtering)
            calculator: KPI calculator (for recalculating on filter change)
        """
        self.config = config
        self.kpi_data = kpi_data or {}
        self.original_kpi_data = deepcopy(kpi_data) if kpi_data else {}  # Preserve original for filtering
        self.db = db
        self.calculator = calculator
        self.logger = logging.getLogger(__name__)

        # Initialize filter state
        self.selected_projects = ["CCT", "SCPX", "CCEN"]
        self.date_range = 90

        dashboard_config = config.get("dashboard", {})
        self.title = dashboard_config.get("title", "Platform Engineering KPI Dashboard")

        # Initialize Dash app with Bootstrap theme
        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )
        self.app.title = self.title

        self._build_layout()
        self._setup_callbacks()

    def _build_layout(self):
        """Build dashboard layout"""

        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1(self.title, className="text-center mb-4 mt-4"),
                    html.P(
                        "Leadership-Only Dashboard | Team-Level Metrics | Data-Driven Conversations",
                        className="text-center text-muted mb-4"
                    ),
                    html.Hr()
                ])
            ]),

            # Metadata Row
            dbc.Row([
                dbc.Col([
                    html.Div(id="metadata-display", className="mb-4")
                ])
            ]),

            # Filters Row
            dbc.Row([
                dbc.Col([
                    html.Label("Select Projects:", className="fw-bold"),
                    dcc.Dropdown(
                        id="project-filter",
                        options=[
                            {"label": "CCT", "value": "CCT"},
                            {"label": "SCPX", "value": "SCPX"},
                            {"label": "CCEN", "value": "CCEN"}
                        ],
                        value=["CCT", "SCPX", "CCEN"],
                        multi=True,
                        placeholder="Select projects...",
                        className="mb-3"
                    )
                ], width=12, md=6),
                dbc.Col([
                    html.Label("Date Range (days):", className="fw-bold"),
                    dcc.Dropdown(
                        id="date-range-filter",
                        options=[
                            {"label": "Last 30 days", "value": 30},
                            {"label": "Last 60 days", "value": 60},
                            {"label": "Last 90 days", "value": 90},
                            {"label": "Last 180 days", "value": 180},
                            {"label": "Annual (365 days)", "value": 365}
                        ],
                        value=90,
                        clearable=False,
                        className="mb-3"
                    )
                ], width=12, md=6)
            ], className="mb-4"),

            # KPI Tabs
            dbc.Row([
                dbc.Col([
                    dcc.Tabs(id="kpi-tabs", value="overview", children=[
                        dcc.Tab(label="📊 Overview", value="overview"),
                        dcc.Tab(label="📁 By Project", value="by_project"),
                        dcc.Tab(label="🎯 Sprint Predictability", value="sprint_predictability"),
                        dcc.Tab(label="📈 Story Spillover", value="story_spillover"),
                        dcc.Tab(label="⏱️ Cycle Time", value="cycle_time"),
                        dcc.Tab(label="🔀 Work Mix", value="work_mix"),
                        dcc.Tab(label="⚠️ Unplanned Work", value="unplanned_work"),
                        dcc.Tab(label="🔄 Reopened Stories", value="reopened_stories"),
                    ])
                ])
            ]),

            # Content Area
            dbc.Row([
                dbc.Col([
                    html.Div(id="tab-content", className="mt-4")
                ])
            ]),

            # Footer
            dbc.Row([
                dbc.Col([
                    html.Hr(),
                    html.P(
                        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                        "Platform Engineering KPI Dashboard v1.0",
                        className="text-center text-muted small mt-4 mb-4"
                    )
                ])
            ])
        ], fluid=True)

    def _setup_callbacks(self):
        """Setup dashboard callbacks"""

        @self.app.callback(
            Output("tab-content", "children"),
            [Input("kpi-tabs", "value"),
             Input("project-filter", "value"),
             Input("date-range-filter", "value")],
            prevent_initial_call=False
        )
        def render_tab_content(active_tab, selected_projects, date_range):
            """Render content based on selected tab and filters"""
            # Store filter values for use in render methods
            self.selected_projects = selected_projects if selected_projects else []
            self.date_range = date_range if date_range else 90

            self.logger.info(f"Callback triggered - tab: {active_tab}, projects: {self.selected_projects}")

            # Filter KPI data based on selected projects
            self._apply_filters()

            # Add timestamp to force re-render
            timestamp = datetime.now().isoformat()

            content = None
            if active_tab == "overview":
                content = self._render_overview()
            elif active_tab == "by_project":
                content = self._render_by_project()
            elif active_tab == "sprint_predictability":
                content = self._render_sprint_predictability()
            elif active_tab == "story_spillover":
                content = self._render_story_spillover()
            elif active_tab == "cycle_time":
                content = self._render_cycle_time()
            elif active_tab == "work_mix":
                content = self._render_work_mix()
            elif active_tab == "unplanned_work":
                content = self._render_unplanned_work()
            elif active_tab == "reopened_stories":
                content = self._render_reopened_stories()
            else:
                content = html.Div("Select a tab")

            # Wrap content with hidden timestamp to force update
            return html.Div([
                html.Div(timestamp, style={'display': 'none'}, id='timestamp-' + timestamp.replace(':', '-')),
                content
            ])


        @self.app.callback(
            Output("metadata-display", "children"),
            [Input("project-filter", "value"),
             Input("date-range-filter", "value")]
        )
        def render_metadata(selected_projects, date_range):
            """Render metadata display"""
            if not self.kpi_data:
                return dbc.Alert("No data loaded. Please run data collection first.", color="warning")

            generated_at = self.kpi_data.get("generated_at", "Unknown")

            # Show selected projects or all
            if selected_projects:
                projects = ", ".join(selected_projects)
            else:
                projects = ", ".join(self.kpi_data.get("projects", []))

            # Show selected date range
            date_range_days = date_range if date_range else 90

            # Get database stats
            stats = self.kpi_data.get("database_stats", {})

            return dbc.Alert([
                html.Strong("Filters: "),
                f"Projects: {projects} | ",
                f"Date Range: {date_range_days} days | ",
                html.Strong("Database: "),
                f"{stats.get('issues_count', 0)} issues | ",
                html.Strong("Generated: "),
                f"{generated_at[:19]}"
            ], color="info", className="text-center")

    def _apply_filters(self):
        """Apply filters to KPI data based on selected projects and date range"""
        self.logger.info(f"_apply_filters called with projects: {self.selected_projects}, date_range: {self.date_range}")

        if not self.selected_projects:
            self.logger.warning("No projects selected, skipping filter")
            return

        # If calculator is available and date range is different from default, recalculate
        if self.calculator and self.date_range and self.date_range != 365:
            self.logger.info(f"Recalculating KPIs with date_range={self.date_range} days and projects={self.selected_projects}")
            try:
                # Recalculate KPIs with filters
                filtered_data = self.calculator.calculate_all_kpis(
                    date_range_days=self.date_range,
                    projects=self.selected_projects
                )

                # Update kpi_data with recalculated values
                self.kpi_data['kpis'] = filtered_data.get('kpis', {})
                self.kpi_data['kpis_by_project'] = filtered_data.get('kpis_by_project', {})

                # Log recalculated values
                kpis = filtered_data.get('kpis', {})
                self.logger.info(f"✅ Recalculation complete:")
                self.logger.info(f"   Work Mix: {kpis.get('work_mix', {}).get('total_issues', 0)} issues")
                self.logger.info(f"   Cycle Time: {kpis.get('cycle_time', {}).get('average_cycle_time_days', 0):.1f} days ({kpis.get('cycle_time', {}).get('issues_analyzed', 0)} issues)")
                self.logger.info(f"   Sprint Pred: {kpis.get('sprint_predictability', {}).get('overall_average', 0)}%")
                return
            except Exception as e:
                self.logger.error(f"Error recalculating KPIs: {e}")
                # Fall through to aggregation method

        # Fallback: Get per-project KPIs from original unfiltered data and aggregate
        kpis_by_project = self.original_kpi_data.get('kpis_by_project', {})
        self.logger.info(f"Available projects in original data: {list(kpis_by_project.keys())}")

        # Filter to selected projects only
        filtered_kpis_by_project = {
            project: kpis for project, kpis in kpis_by_project.items()
            if project in self.selected_projects
        }

        # Aggregate KPIs across selected projects
        # For now, we'll average numeric values and combine lists
        aggregated_kpis = {}

        # Sprint Predictability - average across projects
        sprint_pred_values = []
        sprint_pred_sprints = []
        for project in self.selected_projects:
            if project in filtered_kpis_by_project:
                sp = filtered_kpis_by_project[project].get('sprint_predictability', {})
                if sp.get('overall_average', 0) > 0:
                    sprint_pred_values.append(sp.get('overall_average', 0))
                    # Add sprints with project name as board_name if missing
                    for sprint in sp.get('sprints', []):
                        sprint_copy = sprint.copy()
                        if 'board_name' not in sprint_copy:
                            sprint_copy['board_name'] = project
                        if 'project' not in sprint_copy:
                            sprint_copy['project'] = project
                        sprint_pred_sprints.append(sprint_copy)

        aggregated_kpis['sprint_predictability'] = {
            'overall_average': round(sum(sprint_pred_values) / len(sprint_pred_values), 1) if sprint_pred_values else 0,
            'sprints': sprint_pred_sprints[:20]  # Limit to 20 sprints for display
        }

        # Story Spillover - sum across projects
        spillover_count = 0
        spillover_total = 0
        spillover_issues = []
        for project in self.selected_projects:
            if project in filtered_kpis_by_project:
                ss = filtered_kpis_by_project[project].get('story_spillover', {})
                spillover_count += ss.get('spillover_count', 0)
                spillover_total += ss.get('total_analyzed', 0)
                spillover_issues.extend(ss.get('spillover_issues', []))

        aggregated_kpis['story_spillover'] = {
            'spillover_percentage': round((spillover_count / spillover_total * 100) if spillover_total > 0 else 0, 1),
            'spillover_count': spillover_count,
            'total_analyzed': spillover_total,
            'spillover_issues': spillover_issues[:50]
        }

        # Cycle Time - weighted average across projects
        total_issues = 0
        total_cycle_time = 0
        all_cycle_times = []
        for project in self.selected_projects:
            if project in filtered_kpis_by_project:
                ct = filtered_kpis_by_project[project].get('cycle_time', {})
                issues_analyzed = ct.get('issues_analyzed', 0)
                if issues_analyzed > 0:
                    total_issues += issues_analyzed
                    total_cycle_time += ct.get('average_cycle_time_days', 0) * issues_analyzed
                    all_cycle_times.extend(ct.get('cycle_times', []))

        all_cycle_times.sort()
        median = all_cycle_times[len(all_cycle_times) // 2] if all_cycle_times else 0

        # Use unfiltered min/max if per-project data doesn't have individual cycle times
        original_ct = self.original_kpi_data.get('kpis', {}).get('cycle_time', {})

        aggregated_kpis['cycle_time'] = {
            'average_cycle_time_days': round(total_cycle_time / total_issues, 1) if total_issues > 0 else 0,
            'median_cycle_time_days': median,
            'min_cycle_time_days': min(all_cycle_times) if all_cycle_times else original_ct.get('min_cycle_time_days', 0),
            'max_cycle_time_days': max(all_cycle_times) if all_cycle_times else original_ct.get('max_cycle_time_days', 0),
            'issues_analyzed': total_issues,
            'cycle_times': all_cycle_times
        }

        # Work Mix - sum across projects
        work_mix_dist = {}
        work_mix_total = 0
        for project in self.selected_projects:
            if project in filtered_kpis_by_project:
                wm = filtered_kpis_by_project[project].get('work_mix', {})
                work_mix_total += wm.get('total_issues', 0)
                for category, data in wm.get('distribution', {}).items():
                    if category not in work_mix_dist:
                        work_mix_dist[category] = {'count': 0}
                    work_mix_dist[category]['count'] += data.get('count', 0)

        # Recalculate percentages
        for category in work_mix_dist:
            work_mix_dist[category]['percentage'] = round(
                (work_mix_dist[category]['count'] / work_mix_total * 100) if work_mix_total > 0 else 0, 1
            )

        aggregated_kpis['work_mix'] = {
            'total_issues': work_mix_total,
            'distribution': work_mix_dist
        }

        # Unplanned Work - average across projects
        unplanned_values = []
        unplanned_sprints = []
        for project in self.selected_projects:
            if project in filtered_kpis_by_project:
                uw = filtered_kpis_by_project[project].get('unplanned_work', {})
                if uw.get('overall_average', 0) > 0:
                    unplanned_values.append(uw.get('overall_average', 0))
                    unplanned_sprints.extend(uw.get('sprints', []))

        aggregated_kpis['unplanned_work'] = {
            'overall_average': round(sum(unplanned_values) / len(unplanned_values), 1) if unplanned_values else 0,
            'sprints': unplanned_sprints
        }

        # Reopened Stories - sum across projects
        reopened_count = 0
        reopened_total = 0
        reopened_issues_list = []
        for project in self.selected_projects:
            if project in filtered_kpis_by_project:
                rs = filtered_kpis_by_project[project].get('reopened_stories', {})
                reopened_count += rs.get('reopened_count', 0)
                reopened_total += rs.get('total_completed', 0)
                reopened_issues_list.extend(rs.get('reopened_issues', []))

        aggregated_kpis['reopened_stories'] = {
            'reopened_percentage': round((reopened_count / reopened_total * 100) if reopened_total > 0 else 0, 1),
            'reopened_count': reopened_count,
            'total_completed': reopened_total,
            'reopened_issues': reopened_issues_list[:50]
        }

        # Update the main kpis with aggregated data
        self.kpi_data['kpis'] = aggregated_kpis
        self.kpi_data['kpis_by_project'] = filtered_kpis_by_project

        # Log aggregated results
        self.logger.info(f"Filter applied - Sprint Predictability: {aggregated_kpis.get('sprint_predictability', {}).get('overall_average', 0)}%")
        self.logger.info(f"Filter applied - Work Mix total: {aggregated_kpis.get('work_mix', {}).get('total_issues', 0)} issues")
        self.logger.info(f"Filter applied - Cycle Time avg: {aggregated_kpis.get('cycle_time', {}).get('average_cycle_time_days', 0)} days")

    def _render_overview(self):
        """Render overview dashboard"""
        if not self.kpi_data.get("kpis"):
            return html.Div("No KPI data available")

        kpis = self.kpi_data.get("kpis", {})

        # Add DEBUG filter status indicator
        filter_status = dbc.Alert([
            html.Strong("🔍 Current Filter State: "),
            f"Projects: {', '.join(self.selected_projects) if self.selected_projects else 'All'} | ",
            f"Sprint Pred: {kpis.get('sprint_predictability', {}).get('overall_average', 0)}% | ",
            f"Work Mix: {kpis.get('work_mix', {}).get('total_issues', 0)} issues | ",
            f"Cycle Time: {kpis.get('cycle_time', {}).get('average_cycle_time_days', 0):.1f} days"
        ], color="warning", className="mb-3")

        # Create summary cards
        cards = [filter_status]  # Add filter status as first "card"

        # KPI 1: Sprint Predictability
        if "sprint_predictability" in kpis:
            sp_data = kpis["sprint_predictability"]
            avg = sp_data.get("overall_average", 0)
            color = "success" if avg >= 70 else "warning" if avg >= 50 else "danger"
            cards.append(self._create_kpi_card(
                "Sprint Predictability",
                f"{avg}%",
                "Avg completion rate",
                color
            ))

        # KPI 2: Story Spillover
        if "story_spillover" in kpis:
            ss_data = kpis["story_spillover"]
            pct = ss_data.get("spillover_percentage", 0)
            color = "success" if pct <= 20 else "warning" if pct <= 30 else "danger"
            cards.append(self._create_kpi_card(
                "Story Spillover",
                f"{pct}%",
                "Stories spanning >2 sprints",
                color
            ))

        # KPI 3: Cycle Time
        if "cycle_time" in kpis:
            ct_data = kpis["cycle_time"]
            avg = ct_data.get("average_cycle_time_days", 0)
            color = "success" if avg <= 10 else "warning" if avg <= 20 else "danger"
            cards.append(self._create_kpi_card(
                "Avg Cycle Time",
                f"{avg} days",
                "In Progress → Done",
                color
            ))

        # KPI 5: Unplanned Work
        if "unplanned_work" in kpis:
            uw_data = kpis["unplanned_work"]
            avg = uw_data.get("overall_average", 0)
            color = "success" if avg <= 20 else "warning" if avg <= 30 else "danger"
            cards.append(self._create_kpi_card(
                "Unplanned Work",
                f"{avg}%",
                "Interrupt work load",
                color
            ))

        # KPI 6: Reopened Stories
        if "reopened_stories" in kpis:
            rs_data = kpis["reopened_stories"]
            pct = rs_data.get("reopened_percentage", 0)
            color = "success" if pct <= 10 else "warning" if pct <= 20 else "danger"
            cards.append(self._create_kpi_card(
                "Reopened Stories",
                f"{pct}%",
                "Issues reopened after Done",
                color
            ))

        # Work Mix (show as small pie chart)
        work_mix_chart = None
        if "work_mix" in kpis:
            work_mix_chart = self._create_work_mix_pie_chart(kpis["work_mix"])

        return html.Div([
            html.H3("KPI Summary", className="mb-4"),
            dbc.Row([
                dbc.Col(card, width=12, md=6, lg=4, className="mb-3")
                for card in cards
            ]),
            html.Hr(className="my-4"),
            html.H3("Work Mix Distribution", className="mb-4"),
            dcc.Graph(figure=work_mix_chart) if work_mix_chart else html.Div("No work mix data"),
            html.Hr(className="my-4"),
            dbc.Alert([
                html.H5("Dashboard Principles", className="alert-heading"),
                html.Ul([
                    html.Li("Team-level metrics only (monthly trends)"),
                    html.Li("Metrics drive conversations, not judgments"),
                    html.Li("Identify where teams need help, not where people are failing"),
                    html.Li("Any metric without EM context is considered invalid")
                ])
            ], color="light")
        ])

    def _create_kpi_card(self, title: str, value: str, subtitle: str, color: str = "primary"):
        """Create a KPI summary card"""
        return dbc.Card([
            dbc.CardBody([
                html.H5(title, className="card-title"),
                html.H2(value, className=f"text-{color}"),
                html.P(subtitle, className="text-muted small")
            ])
        ], className="shadow-sm")

    def _render_by_project(self):
        """Render KPIs broken down by project"""
        if "kpis_by_project" not in self.kpi_data:
            return html.Div("No project-level data available")

        kpis_by_project = self.kpi_data["kpis_by_project"]
        all_projects = self.kpi_data.get("projects", [])

        # Filter to selected projects
        if hasattr(self, 'selected_projects') and self.selected_projects:
            projects = [p for p in all_projects if p in self.selected_projects]
        else:
            # Default: show only CCT, SCPX, CCEN
            allowed_projects = ["CCT", "SCPX", "CCEN"]
            projects = [p for p in all_projects if p in allowed_projects]

        if not projects:
            return dbc.Alert([
                html.H5("No Data Available", className="alert-heading"),
                html.P(f"Selected projects: {', '.join(self.selected_projects if hasattr(self, 'selected_projects') else [])}"),
                html.P(f"Available projects in database: {', '.join(all_projects)}"),
                html.Hr(),
                html.P("Try selecting different projects or run data sync to get more data.", className="mb-0")
            ], color="warning")

        # Create project selector and content
        sections = []

        sections.append(html.H3("KPIs by Project", className="mb-4"))
        sections.append(html.P("View metrics broken down by individual projects", className="text-muted"))

        # Add filter indicator
        filter_banner = dbc.Alert([
            html.Strong("🔍 Active Filters: "),
            f"Projects: {', '.join(projects)} | ",
            f"Date Range: {self.date_range} days | ",
            f"Showing {len(projects)} project(s)"
        ], color="light", className="mb-3")
        sections.append(filter_banner)

        self.logger.info(f"📊 Rendering By Project: {len(projects)} projects - {', '.join(projects)}")

        # Create cards for each project
        for project in projects:
            project_data = kpis_by_project.get(project, {})

            if not project_data:
                continue

            # Extract metrics
            sprint_pred = project_data.get("sprint_predictability", {})
            spillover = project_data.get("story_spillover", {})
            cycle_time = project_data.get("cycle_time", {})
            work_mix = project_data.get("work_mix", {})
            reopened = project_data.get("reopened_stories", {})

            # Create summary cards for this project
            project_cards = dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("Sprint Predictability", className="card-subtitle mb-2 text-muted"),
                        html.H3(f"{sprint_pred.get('overall_average', 0)}%",
                               className=self._get_color_class(sprint_pred.get('overall_average', 0), 70, 50))
                    ])
                ]), width=6, lg=3),
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("Story Spillover", className="card-subtitle mb-2 text-muted"),
                        html.H3(f"{spillover.get('spillover_percentage', 0)}%",
                               className=self._get_color_class(spillover.get('spillover_percentage', 0), 20, 30, inverse=True))
                    ])
                ]), width=6, lg=3),
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("Avg Cycle Time", className="card-subtitle mb-2 text-muted"),
                        html.H3(f"{cycle_time.get('average_cycle_time_days', 0)} days",
                               className=self._get_color_class(cycle_time.get('average_cycle_time_days', 0), 10, 20, inverse=True))
                    ])
                ]), width=6, lg=3),
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("Reopened Stories", className="card-subtitle mb-2 text-muted"),
                        html.H3(f"{reopened.get('reopened_percentage', 0)}%",
                               className=self._get_color_class(reopened.get('reopened_percentage', 0), 10, 20, inverse=True))
                    ])
                ]), width=6, lg=3),
            ], className="mb-3")

            # Work mix chart for this project
            work_mix_chart = None
            if work_mix.get('total_issues', 0) > 0:
                distribution = work_mix.get('distribution', {})
                labels = [cat.replace("_", " ").title() for cat in distribution.keys()]
                values = [data["count"] for data in distribution.values()]

                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.3,
                    textinfo="label+percent"
                )])
                fig.update_layout(
                    title=f"Work Mix Distribution - {project}",
                    height=400
                )
                work_mix_chart = dcc.Graph(figure=fig)

            # Add project section
            sections.append(html.Hr(className="my-4"))
            sections.append(html.H4(f"Project: {project}", className="mb-3"))
            sections.append(project_cards)
            if work_mix_chart:
                sections.append(work_mix_chart)

            # Add issue counts
            sections.append(dbc.Alert([
                html.Strong(f"Issues Analyzed: "),
                f"{spillover.get('total_analyzed', 0)} stories | ",
                f"{cycle_time.get('issues_analyzed', 0)} completed | ",
                f"{work_mix.get('total_issues', 0)} total"
            ], color="info", className="mt-3"))

        return html.Div(sections)

    def _get_color_class(self, value: float, good_threshold: float, bad_threshold: float, inverse: bool = False) -> str:
        """Get Bootstrap color class based on value"""
        if not inverse:
            if value >= good_threshold:
                return "text-success"
            elif value >= bad_threshold:
                return "text-warning"
            else:
                return "text-danger"
        else:
            if value <= good_threshold:
                return "text-success"
            elif value <= bad_threshold:
                return "text-warning"
            else:
                return "text-danger"

    def _render_sprint_predictability(self):
        """Render Sprint Predictability KPI"""
        if "sprint_predictability" not in self.kpi_data.get("kpis", {}):
            return html.Div("No sprint predictability data available")

        sp_data = self.kpi_data["kpis"]["sprint_predictability"]

        # Add filter indicator
        filter_banner = dbc.Alert([
            html.Strong("🔍 Filters: "),
            f"Projects: {', '.join(self.selected_projects) if self.selected_projects else 'All'} | ",
            f"Average: {sp_data.get('overall_average', 0)}% | ",
            f"Sprints Analyzed: {len(sp_data.get('sprints', []))}"
        ], color="light", className="mb-3")

        # Create bar chart
        sprints = sp_data.get("sprints", [])
        if not sprints:
            return html.Div([
                html.H3("KPI 1: Sprint Predictability", className="mb-4"),
                filter_banner,
                dbc.Alert("No sprint data available for selected filters", color="warning")
            ])

        sprint_names = [s["sprint_name"] for s in sprints]
        completion_rates = [s["completion_rate"] for s in sprints]
        committed = [s["committed"] for s in sprints]
        completed = [s["completed"] for s in sprints]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name="Completion Rate",
            x=sprint_names,
            y=completion_rates,
            text=[f"{rate}%" for rate in completion_rates],
            textposition="outside",
            marker_color=['green' if r >= 70 else 'orange' if r >= 50 else 'red' for r in completion_rates]
        ))

        fig.update_layout(
            title="Sprint Predictability - Completion Rate by Sprint",
            xaxis_title="Sprint",
            yaxis_title="Completion Rate (%)",
            yaxis=dict(range=[0, 110]),
            height=500
        )

        # Create details table
        table = dbc.Table([
            html.Thead(html.Tr([
                html.Th("Sprint"),
                html.Th("Board"),
                html.Th("Committed"),
                html.Th("Completed"),
                html.Th("Rate")
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(s["sprint_name"]),
                    html.Td(s["board_name"]),
                    html.Td(s["committed"]),
                    html.Td(s["completed"]),
                    html.Td(f"{s['completion_rate']}%", className=self._get_status_class(s["completion_rate"], 70, 50))
                ]) for s in sprints
            ])
        ], bordered=True, hover=True, striped=True)

        return html.Div([
            html.H3("KPI 1: Sprint Predictability", className="mb-4"),
            html.P("Measures % of committed stories completed within sprint"),
            filter_banner,
            dbc.Alert(f"Overall Average: {sp_data.get('overall_average', 0)}%", color="info"),
            dcc.Graph(figure=fig),
            html.H4("Sprint Details", className="mt-4 mb-3"),
            table
        ])

    def _render_story_spillover(self):
        """Render Story Spillover KPI"""
        if "story_spillover" not in self.kpi_data.get("kpis", {}):
            return html.Div("No story spillover data available")

        ss_data = self.kpi_data["kpis"]["story_spillover"]

        # Log what we're rendering
        self.logger.info(f"📊 Rendering Story Spillover: {ss_data.get('total_analyzed', 0)} analyzed, {ss_data.get('spillover_count', 0)} spillover")

        # Add filter indicator
        filter_banner = dbc.Alert([
            html.Strong("🔍 Active Filters: "),
            f"Projects: {', '.join(self.selected_projects) if self.selected_projects else 'All'} | ",
            f"Date Range: {self.date_range} days | ",
            f"Stories Analyzed: {ss_data.get('total_analyzed', 0)} | ",
            f"Spillover: {ss_data.get('spillover_count', 0)} ({ss_data.get('spillover_percentage', 0)}%)"
        ], color="light", className="mb-3")

        spillover_issues = ss_data.get("spillover_issues", [])

        # Create summary metrics
        metrics = dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4(ss_data.get("total_analyzed", 0)),
                    html.P("Total Stories Analyzed", className="text-muted")
                ])
            ]), width=4),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4(ss_data.get("spillover_count", 0)),
                    html.P("Spillover Stories", className="text-muted")
                ])
            ]), width=4),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4(f"{ss_data.get('spillover_percentage', 0)}%"),
                    html.P("Spillover Rate", className="text-muted")
                ])
            ]), width=4)
        ], className="mb-4")

        # Create table of spillover issues
        if spillover_issues:
            table = dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Issue Key"),
                    html.Th("Summary"),
                    html.Th("Sprint Count"),
                    html.Th("Status")
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(html.A(issue["key"], href=f"#", target="_blank")),
                        html.Td(issue["summary"]),
                        html.Td(issue["sprint_count"]),
                        html.Td(issue["status"])
                    ]) for issue in spillover_issues[:50]  # Limit to 50
                ])
            ], bordered=True, hover=True, striped=True)
        else:
            table = dbc.Alert("No spillover issues found - Great!", color="success")

        return html.Div([
            html.H3("KPI 2: Story Spillover", className="mb-4"),
            html.P("Measures % of stories spanning more than 2 sprints"),
            filter_banner,
            metrics,
            html.H4("Spillover Issues", className="mt-4 mb-3"),
            table
        ])

    def _render_cycle_time(self):
        """Render Cycle Time KPI"""
        if "cycle_time" not in self.kpi_data.get("kpis", {}):
            return html.Div("No cycle time data available")

        ct_data = self.kpi_data["kpis"]["cycle_time"]

        # Create metrics
        metrics = dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4(f"{ct_data.get('average_cycle_time_days', 0)} days"),
                    html.P("Average Cycle Time", className="text-muted")
                ])
            ]), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4(f"{ct_data.get('median_cycle_time_days', 0)} days"),
                    html.P("Median Cycle Time", className="text-muted")
                ])
            ]), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4(f"{ct_data.get('min_cycle_time_days', 0)} days"),
                    html.P("Min Cycle Time", className="text-muted")
                ])
            ]), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4(f"{ct_data.get('max_cycle_time_days', 0)} days"),
                    html.P("Max Cycle Time", className="text-muted")
                ])
            ]), width=3)
        ], className="mb-4")

        # Create histogram
        cycle_times = ct_data.get("cycle_times", [])
        if cycle_times:
            times = [ct["cycle_time_days"] for ct in cycle_times]
            fig = px.histogram(
                x=times,
                nbins=20,
                title="Cycle Time Distribution",
                labels={"x": "Cycle Time (days)", "y": "Number of Issues"}
            )
            fig.update_layout(height=400)
            chart = dcc.Graph(figure=fig)
        else:
            chart = dbc.Alert("No cycle time data available", color="warning")

        # Get top 5 longest cycle time stories
        top_5_section = None
        if cycle_times:
            sorted_times = sorted(cycle_times, key=lambda x: x.get('cycle_time_days', 0), reverse=True)[:5]

            top_5_table = dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Rank"),
                    html.Th("Issue Key"),
                    html.Th("Cycle Time (days)")
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(f"#{i+1}"),
                        html.Td(ct.get("issue_key", "N/A")),
                        html.Td(f"{ct.get('cycle_time_days', 0)} days", className="text-danger" if ct.get('cycle_time_days', 0) > 60 else "")
                    ]) for i, ct in enumerate(sorted_times)
                ])
            ], bordered=True, hover=True, striped=True, className="mb-4")

            top_5_section = html.Div([
                html.H4("Top 5 Longest Cycle Times", className="mt-4 mb-3"),
                top_5_table
            ])

        return html.Div([
            html.H3("KPI 3: Average Story Cycle Time", className="mb-4"),
            html.P("Measures avg time from 'In Progress' → 'Done'"),
            dbc.Alert(f"Issues Analyzed: {ct_data.get('issues_analyzed', 0)} | Filters: {', '.join(self.selected_projects) if self.selected_projects else 'All'} | {self.date_range} days", color="info"),
            metrics,
            chart,
            top_5_section if top_5_section else html.Div()
        ])

    def _render_work_mix(self):
        """Render Work Mix Distribution KPI"""
        if "work_mix" not in self.kpi_data.get("kpis", {}):
            return html.Div("No work mix data available")

        wm_data = self.kpi_data["kpis"]["work_mix"]

        # Add filter indicator
        filter_banner = dbc.Alert([
            html.Strong("🔍 Active Filters: "),
            f"Projects: {', '.join(self.selected_projects) if self.selected_projects else 'All'} | ",
            f"Date Range: {self.date_range} days | ",
            f"Total Issues: {wm_data.get('total_issues', 0)}"
        ], color="light", className="mb-3")

        self.logger.info(f"📊 Rendering Work Mix: {wm_data.get('total_issues', 0)} total issues")

        # Create pie chart
        fig = self._create_work_mix_pie_chart(wm_data)

        # Create table
        distribution = wm_data.get("distribution", {})
        table = dbc.Table([
            html.Thead(html.Tr([
                html.Th("Category"),
                html.Th("Count"),
                html.Th("Percentage")
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(category.replace("_", " ").title()),
                    html.Td(data["count"]),
                    html.Td(f"{data['percentage']}%")
                ]) for category, data in distribution.items()
            ])
        ], bordered=True, hover=True, striped=True)

        return html.Div([
            html.H3("KPI 4: Work Mix Distribution", className="mb-4"),
            html.P("Measures % of work by category (labels)"),
            filter_banner,
            dcc.Graph(figure=fig),
            html.H4("Distribution Details", className="mt-4 mb-3"),
            table
        ])

    def _create_work_mix_pie_chart(self, wm_data: Dict):
        """Create work mix pie chart"""
        distribution = wm_data.get("distribution", {})

        labels = [cat.replace("_", " ").title() for cat in distribution.keys()]
        values = [data["count"] for data in distribution.values()]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            textinfo="label+percent"
        )])

        fig.update_layout(
            title="Work Mix Distribution by Category",
            height=500
        )

        return fig

    def _render_unplanned_work(self):
        """Render Unplanned Work KPI"""
        if "unplanned_work" not in self.kpi_data.get("kpis", {}):
            return html.Div("No unplanned work data available")

        uw_data = self.kpi_data["kpis"]["unplanned_work"]

        # Add filter indicator
        filter_banner = dbc.Alert([
            html.Strong("🔍 Active Filters: "),
            f"Projects: {', '.join(self.selected_projects) if self.selected_projects else 'All'} | ",
            f"Date Range: {self.date_range} days | ",
            f"Average: {uw_data.get('overall_average', 0)}% | ",
            f"Sprints Analyzed: {len(uw_data.get('sprints', []))}"
        ], color="light", className="mb-3")

        self.logger.info(f"📊 Rendering Unplanned Work: {uw_data.get('overall_average', 0)}% average, {len(uw_data.get('sprints', []))} sprints")

        sprints = uw_data.get("sprints", [])
        if not sprints:
            return html.Div([
                html.H3("KPI 5: Unplanned Work Load", className="mb-4"),
                filter_banner,
                dbc.Alert("No sprint data available for selected filters", color="warning")
            ])

        # Create bar chart
        sprint_names = [s["sprint_name"] for s in sprints]
        unplanned_pcts = [s["unplanned_percentage"] for s in sprints]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name="Unplanned Work %",
            x=sprint_names,
            y=unplanned_pcts,
            text=[f"{pct}%" for pct in unplanned_pcts],
            textposition="outside",
            marker_color=['green' if p <= 20 else 'orange' if p <= 30 else 'red' for p in unplanned_pcts]
        ))

        fig.update_layout(
            title="Unplanned Work Load by Sprint",
            xaxis_title="Sprint",
            yaxis_title="Unplanned Work (%)",
            yaxis=dict(range=[0, max(unplanned_pcts) + 10 if unplanned_pcts else 50]),
            height=500
        )

        # Create details table
        table = dbc.Table([
            html.Thead(html.Tr([
                html.Th("Sprint"),
                html.Th("Board"),
                html.Th("Total Issues"),
                html.Th("Unplanned"),
                html.Th("Unplanned %")
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(s["sprint_name"]),
                    html.Td(s["board_name"]),
                    html.Td(s["total_issues"]),
                    html.Td(s["unplanned_issues"]),
                    html.Td(f"{s['unplanned_percentage']}%", className=self._get_status_class(s["unplanned_percentage"], 20, 30, inverse=True))
                ]) for s in sprints
            ])
        ], bordered=True, hover=True, striped=True)

        return html.Div([
            html.H3("KPI 5: Unplanned Work Load", className="mb-4"),
            html.P("Measures % of stories labeled as unplanned"),
            filter_banner,
            dcc.Graph(figure=fig),
            html.H4("Sprint Details", className="mt-4 mb-3"),
            table
        ])

    def _render_reopened_stories(self):
        """Render Reopened Stories KPI"""
        if "reopened_stories" not in self.kpi_data.get("kpis", {}):
            return html.Div("No reopened stories data available")

        rs_data = self.kpi_data["kpis"]["reopened_stories"]

        # Add filter indicator
        filter_banner = dbc.Alert([
            html.Strong("🔍 Active Filters: "),
            f"Projects: {', '.join(self.selected_projects) if self.selected_projects else 'All'} | ",
            f"Date Range: {self.date_range} days | ",
            f"Reopened: {rs_data.get('reopened_count', 0)} / {rs_data.get('total_completed', 0)} ({rs_data.get('reopened_percentage', 0)}%)"
        ], color="light", className="mb-3")

        self.logger.info(f"📊 Rendering Reopened Stories: {rs_data.get('reopened_count', 0)} reopened out of {rs_data.get('total_completed', 0)} ({rs_data.get('reopened_percentage', 0)}%)")

        # Create metrics
        metrics = dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4(rs_data.get("reopened_count", 0)),
                    html.P("Reopened Issues", className="text-muted")
                ])
            ]), width=4),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4(rs_data.get("total_completed", 0)),
                    html.P("Total Completed", className="text-muted")
                ])
            ]), width=4),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4(f"{rs_data.get('reopened_percentage', 0)}%"),
                    html.P("Reopened Rate", className="text-muted")
                ])
            ]), width=4)
        ], className="mb-4")

        # Create table
        reopened_issues = rs_data.get("reopened_issues", [])
        if reopened_issues:
            table = dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Issue Key"),
                    html.Th("Summary"),
                    html.Th("Current Status"),
                    html.Th("Updated")
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(html.A(issue["key"], href="#", target="_blank")),
                        html.Td(issue["summary"]),
                        html.Td(issue["current_status"]),
                        html.Td(issue["updated"][:10])
                    ]) for issue in reopened_issues[:50]
                ])
            ], bordered=True, hover=True, striped=True)
        else:
            table = dbc.Alert("No reopened issues found - Great!", color="success")

        return html.Div([
            html.H3("KPI 6: Reopened Stories", className="mb-4"),
            html.P("Measures % of issues reopened after Done"),
            filter_banner,
            metrics,
            html.H4("Reopened Issues", className="mt-4 mb-3"),
            table
        ])

    def _render_jql_queries(self):
        """Render all JQL queries used"""
        kpis = self.kpi_data.get("kpis", {})

        sections = []

        for kpi_name, kpi_data in kpis.items():
            jql_queries = kpi_data.get("jql_queries", [])

            if jql_queries:
                query_cards = []

                for idx, query in enumerate(jql_queries):
                    if isinstance(query, dict):
                        purpose = query.get("purpose", "Query")
                        jql = query.get("jql", "")
                        note = query.get("note", "")

                        card = dbc.Card([
                            dbc.CardHeader(f"Query {idx + 1}: {purpose}"),
                            dbc.CardBody([
                                html.Code(jql, className="d-block p-2 bg-light"),
                                html.P(note, className="text-muted small mt-2") if note else None
                            ])
                        ], className="mb-3")

                        query_cards.append(card)

                sections.append(html.Div([
                    html.H4(kpi_name.replace("_", " ").title(), className="mt-4 mb-3"),
                    html.Div(query_cards)
                ]))

        return html.Div([
            html.H3("JQL Queries Reference", className="mb-4"),
            html.P("All JQL queries used to calculate KPIs"),
            html.Div(sections) if sections else dbc.Alert("No queries available", color="info")
        ])

    def _get_status_class(self, value: float, good_threshold: float, bad_threshold: float, inverse: bool = False):
        """Get Bootstrap color class based on value"""
        if not inverse:
            if value >= good_threshold:
                return "text-success"
            elif value >= bad_threshold:
                return "text-warning"
            else:
                return "text-danger"
        else:
            if value <= good_threshold:
                return "text-success"
            elif value <= bad_threshold:
                return "text-warning"
            else:
                return "text-danger"

    def set_kpi_data(self, kpi_data: Dict):
        """Update KPI data"""
        self.kpi_data = kpi_data

    def run(self, host: str = "127.0.0.1", port: int = 8050, debug: bool = False):
        """Run dashboard server"""
        self.logger.info(f"Starting dashboard on {host}:{port}")
        self.app.run_server(host=host, port=port, debug=debug)

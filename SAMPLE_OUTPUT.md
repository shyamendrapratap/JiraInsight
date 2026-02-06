# Sample Output Examples

This document shows example outputs from the Platform Engineering KPI Dashboard.

## Console Output: Test Connection

```bash
$ python src/main.py --test-connection

============================================================
Testing JIRA Connection...
============================================================
Connected to JIRA as: John Doe
✓ JIRA connection successful!
```

## Console Output: Data Collection

```bash
$ python src/main.py --collect-only --summary

============================================================
Testing JIRA Connection...
============================================================
✓ JIRA connection successful!

============================================================
Collecting KPI Data from JIRA...
============================================================

Calculating KPIs...

✓ KPI calculation complete!
  - Generated at: 2024-02-06T14:30:45.123456
  - Projects analyzed: PLATFORM, INFRA, DEVOPS
  - KPIs calculated: 6

✓ KPI data saved to: ./data/exports/kpi_data_20240206_143045.json

============================================================
KPI SUMMARY
============================================================

📊 Sprint Predictability: 78.5%
   Sprints analyzed: 9

📈 Story Spillover: 15.3%
   Spillover issues: 12 / 78

⏱️  Average Cycle Time: 8.2 days
   Median: 6.0 days
   Issues analyzed: 45

🔀 Work Mix Distribution (Total: 156 issues):
   feature_dev: 45.5% (71 issues)
   tech_debt: 22.4% (35 issues)
   reliability_perf: 12.8% (20 issues)
   ops_enablement: 11.5% (18 issues)
   unplanned: 7.7% (12 issues)
   unlabeled: 0.0% (0 issues)

⚠️  Unplanned Work: 8.3%
   Sprints analyzed: 9

🔄 Reopened Stories: 6.2%
   Reopened: 4 / 65

============================================================

✓ Data collection complete. Exiting (--collect-only mode)
```

## Console Output: Starting Dashboard

```bash
$ python src/main.py

============================================================
Testing JIRA Connection...
============================================================
✓ JIRA connection successful!

============================================================
Collecting KPI Data from JIRA...
============================================================

Calculating KPIs...

✓ KPI calculation complete!
  - Generated at: 2024-02-06T14:35:12.789012
  - Projects analyzed: PLATFORM, INFRA, DEVOPS
  - KPIs calculated: 6

============================================================
Starting Platform Engineering KPI Dashboard
============================================================

Dashboard URL: http://127.0.0.1:8050

Press CTRL+C to stop the dashboard

Dash is running on http://127.0.0.1:8050/

 * Serving Flask app 'dashboard'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
```

## Sample JSON Output

```json
{
  "generated_at": "2024-02-06T14:30:45.123456",
  "projects": ["PLATFORM", "INFRA", "DEVOPS"],
  "analysis_period": {
    "sprint_lookback": 3,
    "rolling_days": 90
  },
  "kpis": {
    "sprint_predictability": {
      "kpi_name": "Sprint Predictability",
      "description": "% of committed stories completed within sprint",
      "sprints": [
        {
          "sprint_name": "Sprint 42",
          "board_name": "Platform Team Board",
          "committed": 25,
          "completed": 21,
          "completion_rate": 84.0,
          "jql_committed": "sprint = 342 AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)",
          "jql_completed": "sprint = 342 AND statusCategory = Done AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)"
        },
        {
          "sprint_name": "Sprint 41",
          "board_name": "Platform Team Board",
          "committed": 23,
          "completed": 18,
          "completion_rate": 78.26,
          "jql_committed": "sprint = 341 AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)",
          "jql_completed": "sprint = 341 AND statusCategory = Done AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)"
        },
        {
          "sprint_name": "Sprint 40",
          "board_name": "Platform Team Board",
          "committed": 28,
          "completed": 20,
          "completion_rate": 71.43,
          "jql_committed": "sprint = 340 AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)",
          "jql_completed": "sprint = 340 AND statusCategory = Done AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)"
        }
      ],
      "overall_average": 77.9
    },
    "story_spillover": {
      "kpi_name": "Story Spillover",
      "description": "% of stories spanning more than 2 sprints",
      "spillover_percentage": 15.38,
      "spillover_issues": [
        {
          "key": "PLATFORM-123",
          "summary": "Implement new authentication system",
          "sprint_count": 4,
          "status": "In Progress"
        },
        {
          "key": "PLATFORM-145",
          "summary": "Refactor database layer",
          "sprint_count": 3,
          "status": "In Review"
        }
      ],
      "total_analyzed": 78,
      "spillover_count": 12,
      "jql_queries": [
        {
          "purpose": "Get stories from closed sprints",
          "jql": "sprint in closedSprints() AND type in (Story, Task) AND project in (PLATFORM, INFRA, DEVOPS)"
        }
      ]
    },
    "cycle_time": {
      "kpi_name": "Average Story Cycle Time",
      "description": "Avg time from In Progress → Done",
      "average_cycle_time_days": 8.2,
      "median_cycle_time_days": 6.0,
      "min_cycle_time_days": 2,
      "max_cycle_time_days": 25,
      "issues_analyzed": 45,
      "cycle_times": [
        {
          "key": "PLATFORM-234",
          "cycle_time_days": 5
        },
        {
          "key": "PLATFORM-235",
          "cycle_time_days": 7
        }
      ],
      "jql_queries": [
        {
          "purpose": "Get completed stories for cycle time analysis",
          "jql": "statusCategory = Done AND type in (Story, Task) AND resolved >= -90d AND project in (PLATFORM, INFRA, DEVOPS)"
        }
      ]
    },
    "work_mix": {
      "kpi_name": "Work Mix Distribution",
      "description": "% of work by category (labels)",
      "distribution": {
        "feature_dev": {
          "count": 71,
          "percentage": 45.51
        },
        "tech_debt": {
          "count": 35,
          "percentage": 22.44
        },
        "reliability_perf": {
          "count": 20,
          "percentage": 12.82
        },
        "ops_enablement": {
          "count": 18,
          "percentage": 11.54
        },
        "unplanned": {
          "count": 12,
          "percentage": 7.69
        },
        "unlabeled": {
          "count": 0,
          "percentage": 0.0
        }
      },
      "total_issues": 156,
      "issues_by_label": {
        "feature_dev": 71,
        "tech_debt": 35,
        "reliability_perf": 20,
        "ops_enablement": 18,
        "unplanned": 12
      },
      "unlabeled_count": 0,
      "jql_queries": [
        {
          "purpose": "Get all work items for distribution analysis",
          "jql": "type in (Epic, Story, Task) AND created >= -90d AND project in (PLATFORM, INFRA, DEVOPS)"
        }
      ]
    },
    "unplanned_work": {
      "kpi_name": "Unplanned Work Load",
      "description": "% of stories labeled as unplanned",
      "sprints": [
        {
          "sprint_name": "Sprint 42",
          "board_name": "Platform Team Board",
          "total_issues": 25,
          "unplanned_issues": 2,
          "unplanned_percentage": 8.0,
          "jql_total": "sprint = 342 AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)",
          "jql_unplanned": "sprint = 342 AND labels = unplanned AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)"
        },
        {
          "sprint_name": "Sprint 41",
          "board_name": "Platform Team Board",
          "total_issues": 23,
          "unplanned_issues": 3,
          "unplanned_percentage": 13.04,
          "jql_total": "sprint = 341 AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)",
          "jql_unplanned": "sprint = 341 AND labels = unplanned AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)"
        }
      ],
      "overall_average": 8.33,
      "jql_queries": [
        {
          "sprint": "Sprint 42",
          "jql_total": "sprint = 342 AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)",
          "jql_unplanned": "sprint = 342 AND labels = unplanned AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)"
        }
      ]
    },
    "reopened_stories": {
      "kpi_name": "Reopened Stories",
      "description": "% of issues reopened after Done",
      "reopened_percentage": 6.15,
      "reopened_issues": [
        {
          "key": "PLATFORM-189",
          "summary": "Fix login redirect issue",
          "current_status": "In Progress",
          "updated": "2024-02-05T10:23:45.000+0000"
        },
        {
          "key": "INFRA-234",
          "summary": "Update deployment scripts",
          "current_status": "To Do",
          "updated": "2024-02-04T15:30:12.000+0000"
        }
      ],
      "total_completed": 65,
      "reopened_count": 4,
      "jql_queries": [
        {
          "purpose": "Find issues that were Done but are now NOT Done",
          "jql": "status WAS IN (Done, Closed, Resolved) AND statusCategory != Done AND type in (Story, Task, Bug) AND updated >= -90d AND project in (PLATFORM, INFRA, DEVOPS)"
        },
        {
          "purpose": "Find issues where status changed FROM Done",
          "jql": "status CHANGED FROM Done AND type in (Story, Task, Bug) AND updated >= -90d AND project in (PLATFORM, INFRA, DEVOPS)"
        }
      ]
    }
  }
}
```

## Dashboard Screenshots (Text Description)

### Overview Tab
```
┌─────────────────────────────────────────────────────────┐
│  Platform Engineering KPI Dashboard                     │
│  Leadership-Only Dashboard | Team-Level Metrics         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Analysis: Last 3 sprints | Rolling 90 days             │
│  Projects: PLATFORM, INFRA, DEVOPS                      │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Sprint       │  │ Story        │  │ Avg Cycle    │ │
│  │ Predictability│ │ Spillover    │  │ Time         │ │
│  │              │  │              │  │              │ │
│  │   78.5%      │  │   15.3%      │  │   8.2 days   │ │
│  │ ✓ Good       │  │ ⚠ Warning    │  │ ✓ Good       │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                   │
│  │ Unplanned    │  │ Reopened     │                   │
│  │ Work         │  │ Stories      │                   │
│  │              │  │              │                   │
│  │   8.3%       │  │   6.2%       │                   │
│  │ ✓ Good       │  │ ✓ Good       │                   │
│  └──────────────┘  └──────────────┘                   │
│                                                          │
│  Work Mix Distribution (Pie Chart)                      │
│  ┌────────────────────────────────────────────────┐   │
│  │         ╱╲                                      │   │
│  │        ╱  ╲     45.5% Feature Dev              │   │
│  │       ╱    ╲    22.4% Tech Debt                │   │
│  │      ╱  🟢  ╲   12.8% Reliability              │   │
│  │     ╱        ╲  11.5% Ops Enablement           │   │
│  │    ────────────  7.7% Unplanned                │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Sprint Predictability Tab
```
┌─────────────────────────────────────────────────────────┐
│  KPI 1: Sprint Predictability                           │
│  Measures % of committed stories completed within sprint│
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Overall Average: 77.9%                                 │
│                                                          │
│  Completion Rate by Sprint (Bar Chart)                  │
│  ┌────────────────────────────────────────────────┐   │
│  │ 100% ┤                                          │   │
│  │  90% ┤     ████                                 │   │
│  │  80% ┤     ████  ████                           │   │
│  │  70% ┤     ████  ████  ████                     │   │
│  │  60% ┤                                          │   │
│  │      └──────────────────────────────            │   │
│  │        Sprint  Sprint  Sprint                   │   │
│  │          42     41     40                       │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
│  Sprint Details                                         │
│  ┌────────┬───────────┬──────────┬──────────┬──────┐  │
│  │ Sprint │ Board     │ Commit   │ Complete │ Rate │  │
│  ├────────┼───────────┼──────────┼──────────┼──────┤  │
│  │ S 42   │ Platform  │    25    │    21    │ 84%  │  │
│  │ S 41   │ Platform  │    23    │    18    │ 78%  │  │
│  │ S 40   │ Platform  │    28    │    20    │ 71%  │  │
│  └────────┴───────────┴──────────┴──────────┴──────┘  │
└─────────────────────────────────────────────────────────┘
```

## Log File Sample

```log
2024-02-06 14:30:45,123 - __main__ - INFO - Platform Engineering KPI Dashboard starting...
2024-02-06 14:30:45,234 - config_loader - INFO - Loading configuration from /path/to/config/config.yaml
2024-02-06 14:30:45,345 - config_loader - INFO - Configuration validated successfully
2024-02-06 14:30:45,456 - jira_client - INFO - Connected to JIRA as: John Doe
2024-02-06 14:30:45,567 - kpi_calculator - INFO - Calculating all Platform Engineering KPIs
2024-02-06 14:30:45,678 - kpi_calculator - INFO - Calculating KPI 1: Sprint Predictability
2024-02-06 14:30:46,789 - jira_client - INFO - Retrieved 25 issues from JIRA
2024-02-06 14:30:47,890 - kpi_calculator - INFO - Calculating KPI 2: Story Spillover
2024-02-06 14:30:48,901 - jira_client - INFO - Retrieved 78 issues from JIRA
2024-02-06 14:30:49,012 - kpi_calculator - INFO - Calculating KPI 3: Average Story Cycle Time
2024-02-06 14:30:50,123 - jira_client - INFO - Retrieved 45 issues from JIRA
2024-02-06 14:30:51,234 - kpi_calculator - INFO - Calculating KPI 4: Work Mix Distribution
2024-02-06 14:30:52,345 - jira_client - INFO - Retrieved 156 issues from JIRA
2024-02-06 14:30:53,456 - kpi_calculator - INFO - Calculating KPI 5: Unplanned Work Load
2024-02-06 14:30:54,567 - kpi_calculator - INFO - Calculating KPI 6: Reopened Stories
2024-02-06 14:30:55,678 - jira_client - INFO - Retrieved 4 issues from JIRA
2024-02-06 14:30:56,789 - __main__ - INFO - Starting dashboard on 127.0.0.1:8050
```

## Error Examples

### Configuration Error
```bash
$ python src/main.py

❌ Configuration error: Configuration validation failed:
  - JIRA API token not configured (placeholder value detected)

Please check your configuration file and environment variables.
See config/config.yaml and .env.example for reference.
```

### Connection Error
```bash
$ python src/main.py --test-connection

============================================================
Testing JIRA Connection...
============================================================
✗ JIRA connection error: 401 Unauthorized
```

### No Projects Error
```bash
$ python src/main.py

❌ Configuration error: Configuration validation failed:
  - Missing project keys

Please check your configuration file and environment variables.
See config/config.yaml and .env.example for reference.
```

---

**Sample Output Guide v1.0**
*Platform Engineering KPI Dashboard*

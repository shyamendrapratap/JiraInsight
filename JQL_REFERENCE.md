# JQL Query Reference Guide

This document contains all JQL (JIRA Query Language) queries used in the Platform Engineering KPI Dashboard, organized by KPI.

## Table of Contents
1. [KPI 1: Sprint Predictability](#kpi-1-sprint-predictability)
2. [KPI 2: Story Spillover](#kpi-2-story-spillover)
3. [KPI 3: Average Story Cycle Time](#kpi-3-average-story-cycle-time)
4. [KPI 4: Work Mix Distribution](#kpi-4-work-mix-distribution)
5. [KPI 5: Unplanned Work Load](#kpi-5-unplanned-work-load)
6. [KPI 6: Reopened Stories](#kpi-6-reopened-stories)
7. [Utility Queries](#utility-queries)

---

## KPI 1: Sprint Predictability

### Query 1.1: All Issues Committed to Sprint
**Purpose:** Get all issues that were in the sprint at any point

```jql
sprint = <SPRINT_ID> AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)
```

**Parameters:**
- `<SPRINT_ID>`: Numeric ID of the sprint
- Update project list as needed

**Example:**
```jql
sprint = 123 AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA)
```

---

### Query 1.2: Completed Issues in Sprint
**Purpose:** Get all issues completed within the sprint

```jql
sprint = <SPRINT_ID> AND statusCategory = Done AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)
```

**Example:**
```jql
sprint = 123 AND statusCategory = Done AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA)
```

**Calculation:**
```
Completion Rate = (Completed Issues / Committed Issues) × 100
```

---

## KPI 2: Story Spillover

### Query 2.1: Stories from Closed Sprints
**Purpose:** Get all stories from recently closed sprints for analysis

```jql
sprint in closedSprints() AND type in (Story, Task) AND project in (PLATFORM, INFRA, DEVOPS)
```

**Note:** This query requires post-processing to count the number of sprints each issue appeared in. The sprint field contains an array of all sprints the issue has been part of.

---

### Query 2.2: Alternative - Stories with Sprint History
**Purpose:** Get stories with sprint information for manual analysis

```jql
sprint in closedSprints() AND type in (Story, Task) AND sprint is not EMPTY AND project in (PLATFORM, INFRA, DEVOPS)
```

**Post-Processing Required:**
- Parse the `sprint` field for each issue
- Count unique sprints per issue
- Flag issues with sprint count > 2 (or configured threshold)

**Calculation:**
```
Spillover Rate = (Issues with >2 sprints / Total Issues) × 100
```

---

## KPI 3: Average Story Cycle Time

### Query 3.1: Completed Stories in Time Period
**Purpose:** Get all completed stories for cycle time analysis

```jql
statusCategory = Done AND type in (Story, Task) AND resolved >= -90d AND project in (PLATFORM, INFRA, DEVOPS)
```

**Parameters:**
- `-90d`: Days back to analyze (can be -30d, -60d, etc.)

**Example:**
```jql
statusCategory = Done AND type in (Story, Task) AND resolved >= -90d AND project in (PLATFORM, INFRA)
```

**Post-Processing Required:**
- Fetch changelog for each issue
- Find first transition to "In Progress" (or similar status)
- Find transition to "Done" (or similar status)
- Calculate: Cycle Time = Done Date - In Progress Date

**Alternative Status Names:**
- In Progress: "In Development", "In Review", "Development", etc.
- Done: "Closed", "Resolved", "Done", etc.

---

### Query 3.2: Stories In Progress (Current WIP)
**Purpose:** Get current work-in-progress for WIP analysis

```jql
status in ("In Progress", "In Development", "In Review") AND type in (Story, Task) AND project in (PLATFORM, INFRA, DEVOPS)
```

---

## KPI 4: Work Mix Distribution

### Query 4.1: All Work Items in Period
**Purpose:** Get all epics, stories, and tasks for work mix analysis

```jql
type in (Epic, Story, Task) AND created >= -90d AND project in (PLATFORM, INFRA, DEVOPS)
```

**Parameters:**
- `-90d`: Days back to analyze

**Example:**
```jql
type in (Epic, Story, Task) AND created >= -90d AND project in (PLATFORM, INFRA)
```

---

### Query 4.2: Feature Development Work
**Purpose:** Count issues labeled as feature development

```jql
type in (Epic, Story, Task) AND labels = feature_dev AND created >= -90d AND project in (PLATFORM, INFRA, DEVOPS)
```

---

### Query 4.3: Tech Debt Work
**Purpose:** Count issues labeled as tech debt

```jql
type in (Epic, Story, Task) AND labels = tech_debt AND created >= -90d AND project in (PLATFORM, INFRA, DEVOPS)
```

---

### Query 4.4: Reliability & Performance Work
**Purpose:** Count issues labeled as reliability/performance work

```jql
type in (Epic, Story, Task) AND labels = reliability_perf AND created >= -90d AND project in (PLATFORM, INFRA, DEVOPS)
```

---

### Query 4.5: Ops Enablement Work
**Purpose:** Count issues labeled as ops enablement

```jql
type in (Epic, Story, Task) AND labels = ops_enablement AND created >= -90d AND project in (PLATFORM, INFRA, DEVOPS)
```

---

### Query 4.6: Unplanned Work (in Work Mix)
**Purpose:** Count issues labeled as unplanned

```jql
type in (Epic, Story, Task) AND labels = unplanned AND created >= -90d AND project in (PLATFORM, INFRA, DEVOPS)
```

---

### Query 4.7: Unlabeled Work
**Purpose:** Find work items missing required labels

```jql
type in (Epic, Story, Task) AND created >= -90d AND labels not in (feature_dev, tech_debt, reliability_perf, ops_enablement, unplanned) AND project in (PLATFORM, INFRA, DEVOPS)
```

**Calculation:**
```
Work Mix % = (Issues with Label / Total Issues) × 100
```

---

## KPI 5: Unplanned Work Load

### Query 5.1: Total Issues in Sprint
**Purpose:** Get all issues in a specific sprint

```jql
sprint = <SPRINT_ID> AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)
```

---

### Query 5.2: Unplanned Issues in Sprint
**Purpose:** Get issues labeled as unplanned in a specific sprint

```jql
sprint = <SPRINT_ID> AND labels = unplanned AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)
```

**Example:**
```jql
sprint = 123 AND labels = unplanned AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA)
```

**Calculation:**
```
Unplanned Rate = (Unplanned Issues / Total Issues in Sprint) × 100
```

---

### Query 5.3: Unplanned Work Across Recent Sprints
**Purpose:** Get all unplanned work from closed sprints

```jql
sprint in closedSprints() AND labels = unplanned AND type in (Story, Task, Bug) AND project in (PLATFORM, INFRA, DEVOPS)
```

---

## KPI 6: Reopened Stories

### Query 6.1: Issues Reopened After Done (Primary)
**Purpose:** Find issues that were Done but are now NOT Done

```jql
status WAS IN (Done, Closed, Resolved) AND statusCategory != Done AND type in (Story, Task, Bug) AND updated >= -90d AND project in (PLATFORM, INFRA, DEVOPS)
```

**Parameters:**
- `-90d`: Days back to check

**Example:**
```jql
status WAS IN (Done, Closed, Resolved) AND statusCategory != Done AND type in (Story, Task, Bug) AND updated >= -90d AND project in (PLATFORM, INFRA)
```

---

### Query 6.2: Issues with Status Changed FROM Done
**Purpose:** Find issues where status changed from Done to any other status

```jql
status CHANGED FROM Done AND type in (Story, Task, Bug) AND updated >= -90d AND project in (PLATFORM, INFRA, DEVOPS)
```

**Example:**
```jql
status CHANGED FROM Done AND type in (Story, Task, Bug) AND updated >= -90d AND project in (PLATFORM, INFRA)
```

---

### Query 6.3: Total Completed Issues (Context)
**Purpose:** Get total completed issues for comparison

```jql
statusCategory = Done AND type in (Story, Task, Bug) AND resolved >= -90d AND project in (PLATFORM, INFRA, DEVOPS)
```

**Calculation:**
```
Reopened Rate = (Reopened Issues / (Total Completed + Reopened)) × 100
```

---

## Utility Queries

### Get All Boards for Projects
**Purpose:** Find all Scrum/Kanban boards for your projects

```jql
project in (PLATFORM, INFRA, DEVOPS)
```

Then use: Filter → Boards → View All Boards

---

### Get Closed Sprints
**Purpose:** Find recently closed sprints

Via JIRA REST API:
```
/rest/agile/1.0/board/<BOARD_ID>/sprint?state=closed
```

---

### Get Sprint Information
**Purpose:** Get details about a specific sprint

Via JIRA REST API:
```
/rest/agile/1.0/sprint/<SPRINT_ID>
```

---

### Find Issues Without Required Labels
**Purpose:** Identify epics and stories that need labeling

```jql
type in (Epic, Story) AND labels is EMPTY AND project in (PLATFORM, INFRA, DEVOPS) AND created >= -30d
```

Or find issues without ANY of the required labels:

```jql
type in (Epic, Story) AND labels not in (feature_dev, tech_debt, reliability_perf, ops_enablement, unplanned) AND project in (PLATFORM, INFRA, DEVOPS) AND created >= -30d
```

---

### Get All Issues by Team Member (for EM review)
**Purpose:** Find all issues assigned to a team member (team-level context only)

```jql
assignee = "<EMAIL>" AND project in (PLATFORM, INFRA, DEVOPS) AND resolved >= -90d
```

**Note:** This is for EM context only, not for individual performance tracking.

---

## JQL Tips & Best Practices

### Date Ranges
- `-30d` = Last 30 days
- `-90d` = Last 90 days
- `>= "2024-01-01"` = From specific date
- `>= -7d AND <= -1d` = Last week (excluding today)

### Status Categories vs Status Names
- `statusCategory = Done` (generic, works across all projects)
- `status = "Done"` (specific status name, may vary)

### Multiple Projects
- `project in (PROJ1, PROJ2, PROJ3)`
- `project = PROJ1`

### Issue Types
- `type in (Story, Task, Bug, Epic)`
- `type = Story`

### Labels
- `labels = label_name` (has this label)
- `labels in (label1, label2)` (has any of these)
- `labels is EMPTY` (no labels)
- `labels is not EMPTY` (has at least one label)

### Sprints
- `sprint = 123` (specific sprint)
- `sprint in (123, 124, 125)` (multiple sprints)
- `sprint in openSprints()` (current active sprints)
- `sprint in closedSprints()` (all closed sprints)
- `sprint in futureSprints()` (planned sprints)

### Advanced Operators
- `AND` - Both conditions must be true
- `OR` - Either condition must be true
- `NOT` - Negates a condition
- `()` - Groups conditions

### Example Complex Query
```jql
project in (PLATFORM, INFRA)
AND type in (Story, Task)
AND (
  labels = tech_debt
  OR labels = reliability_perf
)
AND sprint in closedSprints()
AND resolved >= -60d
AND statusCategory = Done
ORDER BY resolved DESC
```

---

## Testing Your Queries

### In JIRA Web UI
1. Go to JIRA → Filters → Advanced Search
2. Paste your JQL query
3. Click "Search"
4. Save as filter if needed

### Via API (curl)
```bash
curl -X GET \
  -H "Content-Type: application/json" \
  --user "your.email@company.com:YOUR_API_TOKEN" \
  "https://your-company.atlassian.net/rest/api/3/search?jql=<YOUR_JQL_QUERY_HERE>&maxResults=10"
```

### Via Python (using requests)
```python
import requests
from requests.auth import HTTPBasicAuth

jql = "project = PLATFORM AND type = Story"
url = "https://your-company.atlassian.net/rest/api/3/search"

response = requests.get(
    url,
    params={"jql": jql, "maxResults": 10},
    auth=HTTPBasicAuth("your.email@company.com", "YOUR_API_TOKEN")
)

print(response.json())
```

---

## Troubleshooting Common Issues

### No Results Returned
- Check project keys are correct (case-sensitive)
- Verify date ranges are valid
- Ensure labels exist in JIRA
- Check you have read permissions

### Too Many Results
- Add date filters (`created >= -90d`)
- Narrow project scope
- Add specific issue types

### Field Not Found
- Some fields are custom fields (e.g., `sprint`)
- Use JIRA Field Configuration to find field names
- Custom fields often start with `cf[xxxxx]`

### Performance Issues
- Add date ranges to limit results
- Use `maxResults` parameter in API calls
- Avoid very broad queries without filters

---

**JQL Reference Guide v1.0**
*Platform Engineering KPI Dashboard*

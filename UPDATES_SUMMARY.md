# Dashboard Updates Summary

## ✅ Changes Completed

### 1. Sample Data Cleaned Up
- **Removed**: 193 sample/test issues
- **Kept**: 686 real JIRA issues from actual sprints
- Database now contains **only real data**

### 2. Project Filtering
**Projects in Database:**
- **SCPX**: 845 issues (primary project)
- **CCT**: 54 issues
- **OPR**: 167 issues (not in configured list)
- **IND**: 7 issues (not in configured list)
- **TFE**: 1 issue (not in configured list)

**Configured Projects** (config/config.yaml):
- CCT
- SCPX
- CCEN (no data currently, but configured for future syncs)

**Dashboard Filtering:**
- Dashboard now shows **only CCT, SCPX, and CCEN** projects
- Other projects (OPR, IND, TFE) are filtered out from display

### 3. New Features Added

#### Project Multi-Select Dropdown
- Located at the top of dashboard
- Allows selecting one or multiple projects
- Default: All three projects (CCT, SCPX, CCEN) selected
- Updates all KPI views based on selection

#### Date Range Dropdown
- Located next to project filter
- Options available:
  - **Last 30 days**
  - **Last 60 days**
  - **Last 90 days** (default)
  - **Last 180 days**
  - **Annual (365 days)**
- Filters data based on issue creation/update dates

#### New "By Project" Tab
- Shows KPIs broken down by individual project
- Displays for each project:
  - Sprint Predictability
  - Story Spillover
  - Average Cycle Time
  - Reopened Stories
  - Work Mix Distribution (pie chart)
  - Issue counts

### 4. Removed Features
- ❌ **JQL Queries Tab** - Removed as requested
- This simplifies the dashboard and removes technical details

### 5. Dashboard Tabs (Updated)
1. **📊 Overview** - All KPIs at a glance
2. **📁 By Project** - KPIs broken down per project (NEW)
3. **🎯 Sprint Predictability** - Completion rates
4. **📈 Story Spillover** - Multi-sprint issues
5. **⏱️ Cycle Time** - Time to completion
6. **🔀 Work Mix** - Work distribution
7. **⚠️ Unplanned Work** - Interrupt work
8. **🔄 Reopened Stories** - Quality metrics

## 📊 Current Data Status

```
Total Issues:   1,074 (real JIRA data)
  - SCPX:       845 issues
  - OPR:        167 issues (filtered out)
  - CCT:        54 issues
  - IND:        7 issues (filtered out)
  - TFE:        1 issue (filtered out)

Displayed Projects: CCT, SCPX (CCEN has no data yet)
Total Sprints:  47
Total Boards:   3
```

## 🎯 How to Use

### Start Dashboard
```bash
python src/main.py --use-db
```

### Access Dashboard
Open: **http://127.0.0.1:8050**

### Using Filters

**1. Project Filter** (top left)
- Click dropdown to select/deselect projects
- Select multiple projects to compare
- Default: All three configured projects

**2. Date Range Filter** (top right)
- Select time period for analysis
- Default: 90 days
- Affects cycle time, work mix, reopened stories calculations

**3. Navigate Tabs**
- Use tabs to view different KPI categories
- "By Project" tab shows side-by-side comparison

## 📈 Data Improvements

### Better Project Representation
- Only configured projects (CCT, SCPX, CCEN) are shown
- Other discovered projects are filtered out
- Clear project-level breakdowns in new tab

### Color Coding
- 🟢 **Green**: Good (meets or exceeds targets)
- 🟡 **Yellow**: Warning (approaching thresholds)
- 🔴 **Red**: Critical (below acceptable levels)

### Issue Counts
Each project view now shows:
- Stories analyzed
- Completed issues
- Total issues in period

## 🔄 Sync More Data for CCEN

Currently CCEN has no issues in the database. To get CCEN data:

```bash
# Sync more sprints (will pull issues from CCEN sprints if they exist)
python sync_from_sprints.py
```

or

```bash
# Sync all 47 sprints
python sync_all_sprints.py
```

## 🎨 Next Steps

To get CCEN data appearing:
1. Verify CCEN project exists in JIRA
2. Check if CCEN issues are in any sprints
3. Run sync_from_sprints.py to pull more data
4. Restart dashboard to see updated data

## 📝 Configuration

Project configuration in `config/config.yaml`:

```yaml
projects:
  project_keys:
    - "CCT"
    - "SCPX"
    - "CCEN"
```

This ensures only these three projects are:
- Queried during sync
- Displayed in dashboard
- Available in dropdowns

## ✨ Summary

**Before:**
- Mixed sample and real data
- All 5 discovered projects shown
- No filtering options
- JQL queries tab present
- No project breakdown view

**After:**
- ✅ Only real JIRA data (686+ issues)
- ✅ Filtered to CCT, SCPX, CCEN only
- ✅ Project multi-select dropdown
- ✅ Date range dropdown (30-365 days)
- ✅ New "By Project" comparison tab
- ✅ JQL Queries tab removed
- ✅ Cleaner, focused dashboard

---

**Dashboard Status:** ✅ Running at http://127.0.0.1:8050
**Last Updated:** 2026-02-07

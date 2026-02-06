# Platform Engineering KPI Dashboard - Current Status

**Date:** 2026-02-07
**Dashboard URL:** http://127.0.0.1:8050

---

## ✅ Successfully Resolved Issues

### 1. CCEN Data - FIXED ✅
**Problem:** CCEN had 0 issues
**Solution:** Synced from CCEN Kanban board (ID: 13644)
**Result:** 49 issues with varied statuses

**CCEN Status Breakdown:**
- Pending Triage: 24
- In Development: 8
- Awaiting Prioritization: 7
- In Discovery: 3
- Blocked: 3
- In Review: 2
- In Progress: 2

### 2. CCT Active Issues - FIXED ✅
**Problem:** CCT only had "Closed" issues, missing In Progress, Pending Triage, etc.
**Solution:** Synced active sprint (Cloud-DR-sprint29) from CCT board (ID: 13679)
**Result:** 176 issues with varied statuses

**CCT Status Breakdown:**
- Closed: 161
- In Progress: 6 ✅
- In Review: 3 ✅
- Pending Triage: 2 ✅
- Blocked: 2 ✅
- To Do: 1 ✅
- Needs More Info: 1 ✅

---

## 📊 Current Database Statistics

```
Total Issues:  1,241
Total Sprints: 73
Total Projects: 4

Project Breakdown:
  - SCPX: 845 issues (full KPI data available)
  - CCT:  176 issues (limited KPI data - see below)
  - CCEN: 49 issues (limited KPI data - see below)
  - SECVULN: 171 issues
```

---

## ⚠️ Why Some KPIs Show 0%

### Sprint Predictability = 0%

**Reason:** This KPI requires **closed sprints** with **issues assigned to those sprints**.

**Current Situation:**
- CCT has 12 sprints (2 active/future, 10 closed)
- **Only 13 out of 176 CCT issues have sprint assignments**
- All 10 closed sprints have **0 issues** in them
- The only sprint with issues is the active sprint (Cloud-DR-sprint29 with 13 issues)

**Why This Happens:**
- Issues on the CCT board exist but aren't formally assigned to sprints
- Board is configured as a "Sprint Board" but used more like a Kanban board
- Sprint Predictability can't be calculated without completed sprints containing issues

**CCEN:**
- Kanban board (no sprints by design)
- Sprint-based metrics don't apply

### Story Spillover = 0%

**Reason:** Requires issues to span multiple sprints.

**Current Situation:**
- 163 out of 176 CCT issues have `sprint_ids = []` (no sprint assignment)
- Only 13 issues have sprint assignment, and they're all in 1 sprint
- Can't calculate spillover if issues aren't moving between sprints

### Reopened Stories = 0%

**Reason:** Requires changelog data to track reopened issues.

**Current Situation:**
- Changelog data may not be available or synced for these boards
- Would need to enable changelog syncing in data collection

---

## ✅ Working KPIs

### 1. Cycle Time ✅
**Status:** Working with limited data

**Results:**
- **CCT:** 56.2 days average (48 issues analyzed)
  - Median: 31.5 days
- **SCPX:** 31.2 days average (400 issues analyzed)
  - Median: 16.0 days
- **CCEN:** 0 days (no completed issues yet to measure)

**Why CCT Works:** Calculates time from creation to resolution for Closed issues.

### 2. Work Mix Distribution ✅
**Status:** Working

**Results:**
- **CCT:** 41 issues analyzed
- **SCPX:** 410 issues analyzed
- **CCEN:** 47 issues analyzed

**Shows:** Distribution by issue type (Story, Bug, Task, etc.)

---

## 🎯 Dashboard Features Currently Available

### Working Features:
1. ✅ **Project Filter Dropdown** - Select CCT, SCPX, CCEN (multi-select)
2. ✅ **Date Range Filter** - 30, 60, 90, 180, 365 days
3. ✅ **Cycle Time Tab** - Shows average cycle times with working data
4. ✅ **Work Mix Tab** - Shows issue type distribution
5. ✅ **By Project Tab** - Side-by-side project comparison
6. ✅ **Real JIRA Data** - All data is from actual JIRA, no sample data

### Limited Features:
- ⚠️ **Sprint Predictability Tab** - Shows 0% (no closed sprints with issues)
- ⚠️ **Story Spillover Tab** - Shows 0% (issues not moving between sprints)
- ⚠️ **Reopened Stories Tab** - Shows 0% (no changelog data)
- ⚠️ **Unplanned Work Tab** - Shows 0% (requires sprint planning data)

---

## 🔍 Root Cause Analysis

### Why Sprint-Based Metrics Don't Work for CCT/CCEN

**CCT Board (13679):**
- Configured as "Sprint Board" in JIRA
- Issues exist on the board but aren't assigned to sprints
- Of 176 issues, only 13 are in a sprint (all in 1 active sprint)
- Closed sprints (28, 27, 26, etc.) have 0 issues
- **Board is being used like Kanban, not sprint planning**

**CCEN Board (13644):**
- Kanban board (no sprints by design)
- 49 issues in various workflow stages
- Sprint-based KPIs don't apply to Kanban boards

**SCPX (for comparison):**
- True sprint planning
- 845 issues across 47 sprints
- Issues properly assigned to sprints
- Sprint-based metrics work correctly

---

## 💡 Recommendations

### Option 1: Accept Current Limitations (Recommended)

**Use available metrics:**
- ✅ Cycle Time (working)
- ✅ Work Mix Distribution (working)
- ✅ Status distribution by project
- ✅ Issue counts and trends

**Focus on:**
- Cycle time improvements
- Work type balance
- Throughput metrics (issues completed per time period)

### Option 2: Change JIRA Workflow

**For sprint-based metrics to work:**
1. Formally plan issues into sprints before starting work
2. Ensure all active work is assigned to the current sprint
3. Complete sprints with committed vs completed tracking
4. This requires team process changes, not just technical changes

### Option 3: Add Kanban-Specific Metrics

**Better suited for CCT/CCEN:**
- Lead Time (total time from created to done)
- Throughput (issues completed per week)
- WIP (work in progress) limits tracking
- Flow efficiency metrics

Would require dashboard modifications to add these metrics.

---

## 📈 What's Working Now

**Dashboard is live with:**
- 1,241 real JIRA issues
- CCT: 176 issues with active statuses ✅
- CCEN: 49 issues from Kanban board ✅
- SCPX: 845 issues with full sprint data ✅
- Cycle Time analysis working ✅
- Work Mix analysis working ✅
- Project filtering working ✅
- Date range filtering working ✅

**Access:** http://127.0.0.1:8050

---

## 🚀 Next Steps

1. **Review dashboard** at http://127.0.0.1:8050
2. **Verify data** matches expectations for CCT, CCEN, SCPX
3. **Decide:** Accept current metrics or request Kanban-specific metrics
4. **Optional:** Adjust team workflow to enable sprint-based metrics

---

## 📝 Technical Details

### Sync Scripts Available:
- `sync_active_sprints.py` - Syncs current + recent closed sprints and CCEN Kanban
- `check_kpi_data.py` - Debug script to verify KPI calculations
- `sync_data.py` - Full database sync

### Database:
- Location: `./data/kpi_data.db`
- Type: SQLite
- Last Sync: 2026-02-07T02:45:16

### Filters:
- Projects: CCT, SCPX, CCEN (configurable in config/config.yaml)
- Date ranges: 30, 60, 90, 180, 365 days
- Default lookback: 365 days for historical data

---

**Status: Dashboard is operational with available data. Sprint-based KPIs limited by workflow practices, not technical issues.**

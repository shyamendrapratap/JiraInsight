# Dashboard Issues - Status & Fixes

**Date:** 2026-02-07

---

## Issues Reported

1. ❌ **Date range filter not working** → Not implemented yet
2. ⚠️ **Sprint Predictability 0% for SCPX** → Data issue (SCPX doesn't use sprint planning)
3. ⚠️ **Story Spillover 0%** → Requires changelog data (not synced)
4. ⚠️ **Reopened Stories 0%** → Requires changelog data (not synced)
5. 🐛 **Cycle Time min/max showing 0 for SCPX** → Bug in filter aggregation

---

## 1. Date Range Filter - NOT IMPLEMENTED ❌

### Status
**Not implemented yet** - dropdown stores value but doesn't recalculate data.

### Why
Current KPIs are pre-calculated at startup with 365-day lookback. Implementing date filtering requires:
- Query database with date filters
- Recalculate all KPIs for that date range
- Significant performance impact

### Workaround
All data uses 365-day lookback currently, which captures your full year of data.

### To Implement (Future)
Would require modifying KPI calculator to accept date range parameters and recalculating on every filter change.

---

## 2. Sprint Predictability 0% for SCPX ⚠️

### Investigation Results

**SCPX Sprint Reports:** All empty (0 committed/0 completed)

```
SCPX Sprint Data:
- Total SCPX issues: 845
- Issues with sprint assignments: 85 (only 10%)
- Sprint reports synced: 15
- All sprint reports: 0/0 (empty)
```

### Root Cause
**SCPX doesn't use formal sprint planning.** The JIRA Sprint Report API returns empty data because:
- Issues exist on board but aren't formally committed to sprints
- SCPX uses Kanban-style workflow, not sprint planning
- Sprint structure exists but isn't used for planning

### Comparison

| Project | Sprint Reports | Sprint Usage |
|---------|---------------|--------------|
| **CCT** | 15 sprints, 71.1% avg | ✅ Active sprint planning |
| **SCPX** | 15 sprints, 0% (empty) | ❌ No sprint planning |
| **CCEN** | 0 sprints (Kanban board) | ❌ Kanban only |

### Resolution
**This is correct behavior** - SCPX doesn't use sprint planning, so Sprint Predictability is not applicable.

### Recommendation
For SCPX, focus on:
- ✅ **Cycle Time:** 31.2 days (working)
- ✅ **Work Mix:** 410 issues (working)
- ✅ **Throughput:** Issues completed per time period

Sprint Predictability is only meaningful for CCT.

---

## 3. Story Spillover 0% ⚠️

### Investigation Results

```sql
SELECT key FROM issues WHERE length(sprint_ids) > 10;
-- Result: 0 rows
```

No issues have multiple sprint IDs in current database.

### Root Cause
**Spillover detection requires changelog data.**

When an issue moves from Sprint A to Sprint B:
- Current snapshot only shows: `sprint_ids = [B]`
- Historical data needed: `Sprint A → Sprint B` (in changelog)

To detect spillover, we need:
1. Issue changelog showing sprint field changes
2. Track when issues moved between sprints
3. Count issues spanning >2 sprints

### Current Data
- ❌ Changelog data not synced
- ✅ Current sprint assignments only
- ❌ No historical sprint movements

### To Fix
Run changelog sync:
```bash
python sync_changelog.py
```

This will:
- Sync issue changelogs for closed issues
- Capture sprint field changes
- Enable spillover detection
- Enable reopened story detection

**Note:** Changelog sync takes ~10-15 minutes for 500 issues.

---

## 4. Reopened Stories 0% ⚠️

### Root Cause
**Same as Story Spillover - requires changelog data.**

To detect reopened stories, we need:
1. Issue status history from changelog
2. Find issues that went: `Done → In Progress` (reopened)

### Current Data
- ❌ Status change history not available
- ✅ Current status only

### To Fix
Same solution as #3: Run `python sync_changelog.py`

---

## 5. Cycle Time Min/Max Showing 0 🐛

### Bug Description
When filtering by project, Cycle Time shows:
- Average: ✅ Correct
- Median: ✅ Correct
- **Min: 0** ❌ Wrong
- **Max: 0** ❌ Wrong

### Root Cause
**Filter aggregation bug.**

Per-project KPI data structure:
```python
{
    'cycle_time': {
        'average_cycle_time_days': 31.2,
        'median_cycle_time_days': 16.0,
        'issues_analyzed': 400,
        # Missing: 'cycle_times' list
        # Missing: 'min_cycle_time_days'
        # Missing: 'max_cycle_time_days'
    }
}
```

Filter aggregation code tries:
```python
ct = project_kpis.get('cycle_time', {})
all_cycle_times.extend(ct.get('cycle_times', []))  # Returns []
min_cycle_time = min(all_cycle_times)  # min([]) = error, defaults to 0
```

### Fix Options

**Option A:** Add min/max to per-project calculations
- Modify `calculate_cycle_time_for_project()` in kpi_calculator_db.py
- Return full cycle_times list and calculate min/max
- More complete but requires recalculation

**Option B:** Use unfiltered data for min/max
- When filtering, keep overall min/max from unfiltered data
- Only recalculate average/median for selected projects
- Faster but less accurate for filtered view

**Option C:** Calculate from unfiltered data filtered in aggregation
- Store all cycle times with project tags in original data
- Filter cycle times by selected projects in _apply_filters()
- Most accurate

### Recommended Fix
**Option B** (pragmatic):
```python
# In _apply_filters(), for cycle time:
original_ct = self.original_kpi_data.get('kpis', {}).get('cycle_time', {})

aggregated_kpis['cycle_time'] = {
    'average_cycle_time_days': ...,  # Calculated from projects
    'median_cycle_time_days': ...,   # Calculated from projects
    'min_cycle_time_days': original_ct.get('min_cycle_time_days', 0),  # Use unfiltered
    'max_cycle_time_days': original_ct.get('max_cycle_time_days', 0),  # Use unfiltered
    'issues_analyzed': total_issues
}
```

**Caveat:** Min/max will be from ALL projects, not just filtered ones. But it's better than showing 0.

---

## Summary of Issues

| Issue | Status | Fix Available | Notes |
|-------|--------|---------------|-------|
| Date filter | ❌ Not implemented | Complex | Would require recalculation |
| SCPX Sprint Pred 0% | ⚠️ Expected | N/A | SCPX doesn't use sprint planning |
| Story Spillover 0% | ⚠️ No data | ✅ Yes | Run sync_changelog.py |
| Reopened 0% | ⚠️ No data | ✅ Yes | Run sync_changelog.py |
| Cycle Time min/max | 🐛 Bug | ✅ Yes | Code fix needed |

---

## Quick Fixes Available Now

### Fix #1: Sync Changelog Data (15 min)
```bash
python sync_changelog.py
```
**Fixes:** Story Spillover & Reopened Stories detection

### Fix #2: Cycle Time Min/Max Bug (2 min)
Update `src/dashboard.py` in `_apply_filters()` method to use unfiltered min/max.

**Fixes:** Cycle Time min/max showing 0

### Fix #3: Update Dashboard Status (1 min)
Restart dashboard after fixes:
```bash
lsof -ti:8050 | xargs kill -9
python src/main.py --use-db
```

---

## What Works Correctly ✅

| Metric | CCT | SCPX | CCEN | Notes |
|--------|-----|------|------|-------|
| Sprint Predictability | ✅ 71.1% | ⚠️ N/A | ⚠️ N/A | Only CCT uses sprints |
| Cycle Time (Avg) | ✅ 51.5d | ✅ 31.2d | ⚠️ 0d | CCEN has no completed issues |
| Work Mix | ✅ 96 | ✅ 410 | ✅ 47 | All working |
| Project Filtering | ✅ Working | ✅ Working | ✅ Working | Backend calculates correctly |

---

## Recommendations

### For Immediate Use
1. **Focus on CCT Sprint Predictability** (71.1%) - this works perfectly
2. **Use SCPX Cycle Time** (31.2 days) - reliable metric
3. **Use Work Mix** for all projects - accurate
4. **Accept SCPX Sprint Pred = 0%** - correct for Kanban workflow

### For Complete Data
1. **Run changelog sync** to enable:
   - Story Spillover detection
   - Reopened Stories detection
2. **Fix cycle time min/max bug** (code change)
3. **Consider** if date range filtering is worth the performance cost

### Alternative Metrics for SCPX/CCEN
Since they don't use sprint planning, consider:
- **Lead Time:** Time from created to done
- **Throughput:** Issues completed per week
- **WIP Limits:** Current in-progress count
- **Flow Efficiency:** Active time vs wait time

These Kanban metrics would be more meaningful than sprint-based metrics.

---

**Dashboard Status:** ✅ Working with expected limitations
**Next Step:** Run `python sync_changelog.py` to enable Story Spillover & Reopened detection

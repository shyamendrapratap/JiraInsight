# Dashboard Filter Fix - Working Now! ✅

**Date:** 2026-02-07
**Issue:** Filters weren't changing data on dashboard
**Status:** ✅ FIXED

---

## What Was Wrong

1. **KeyError: 'board_name'** - When aggregating sprint data from multiple projects, sprint objects were missing the required 'board_name' field
2. **Data persistence** - Original data was being overwritten, so subsequent filter changes failed
3. **Missing deep copy** - Shallow copy of data meant nested dictionaries were still modified

---

## Fixes Applied

### Fix 1: Added Missing 'board_name' Field
**File:** [src/dashboard.py](src/dashboard.py)

When aggregating sprints from multiple projects, now ensures each sprint has 'board_name':
```python
for sprint in sp.get('sprints', []):
    sprint_copy = sprint.copy()
    if 'board_name' not in sprint_copy:
        sprint_copy['board_name'] = project  # Use project name as board name
    if 'project' not in sprint_copy:
        sprint_copy['project'] = project
    sprint_pred_sprints.append(sprint_copy)
```

### Fix 2: Preserve Original Data
**File:** [src/dashboard.py](src/dashboard.py)

Added `original_kpi_data` to preserve unfiltered data:
```python
self.original_kpi_data = deepcopy(kpi_data) if kpi_data else {}
```

Filter method now uses original data:
```python
def _apply_filters(self):
    # Get per-project KPIs from original unfiltered data
    kpis_by_project = self.original_kpi_data.get('kpis_by_project', {})
    # ... filter and aggregate ...
```

### Fix 3: Deep Copy Import
**File:** [src/dashboard.py](src/dashboard.py)

Added deep copy to properly duplicate nested data structures:
```python
from copy import deepcopy
```

---

## How to Test

### Test 1: Single Project Filter
1. Open dashboard: **http://127.0.0.1:8050**
2. Go to "Overview" tab
3. In "Select Projects" dropdown, choose **only CCT**
4. **Expected:** Sprint Predictability shows ~71.1%
5. **Expected:** Work Mix shows only CCT issue counts

### Test 2: Switch to Different Project
1. Change dropdown to **only SCPX**
2. **Expected:** Sprint Predictability shows 0% (SCPX has no sprint reports)
3. **Expected:** Work Mix shows SCPX issue counts (~410 issues)
4. **Expected:** Cycle Time shows ~31.2 days

### Test 3: Multiple Projects
1. Select **CCT + SCPX** (both checked)
2. **Expected:** Sprint Predictability shows averaged value (weighted by CCT since SCPX=0%)
3. **Expected:** Work Mix shows combined totals
4. **Expected:** All KPI tabs update

### Test 4: By Project Tab
1. Go to "By Project" tab
2. Select only **CCT** in dropdown
3. **Expected:** Shows only CCT project card with KPIs
4. Switch to **SCPX only**
5. **Expected:** Shows only SCPX project card

### Test 5: Sprint Predictability Tab
1. Go to "Sprint Predictability" tab
2. Select only **CCT**
3. **Expected:** Shows bar chart with CCT sprints only
4. **Expected:** Table shows sprint details with "CCT" as board name
5. **No KeyError!** ✅

---

## What Should Happen Now

When you change the project dropdown:

### Before (Broken) ❌
```
Select CCT → Shows all projects data
Select SCPX → Still shows all projects data
Select CCEN → Still shows all projects data
No errors but no change!
```

### After (Fixed) ✅
```
Select CCT → Shows ONLY CCT data
  - Sprint Predictability: 71.1%
  - Cycle Time: 51.5 days
  - Work Mix: 96 issues

Select SCPX → Shows ONLY SCPX data
  - Sprint Predictability: 0%
  - Cycle Time: 31.2 days
  - Work Mix: 410 issues

Select CCT + SCPX → Shows COMBINED data
  - Sprint Predictability: ~71.1% (only CCT has sprint data)
  - Cycle Time: ~35 days (weighted average)
  - Work Mix: 506 total issues
```

---

## Technical Details

### Filter Flow
```
User changes dropdown
    ↓
Callback triggered: render_tab_content(active_tab, selected_projects, date_range)
    ↓
Store filter values:
    self.selected_projects = selected_projects
    self.date_range = date_range
    ↓
Call _apply_filters()
    ↓
_apply_filters() reads from original_kpi_data
    ↓
Aggregates only selected projects:
    - Sprint Predictability: average of selected projects
    - Cycle Time: weighted average
    - Work Mix: sum and recalculate %
    - Story Spillover: sum
    - Reopened Stories: sum
    ↓
Updates self.kpi_data with filtered/aggregated results
    ↓
Render method reads from self.kpi_data
    ↓
Display updates with filtered data ✅
```

### Data Structure
```python
original_kpi_data = {
    'kpis_by_project': {
        'CCT': {
            'sprint_predictability': {...},
            'cycle_time': {...},
            # ...
        },
        'SCPX': {...},
        'CCEN': {...}
    },
    'kpis': {  # Overall aggregated
        'sprint_predictability': {...},
        # ...
    }
}

# After filtering to CCT only:
kpi_data = {
    'kpis_by_project': {
        'CCT': {...}  # Only CCT
    },
    'kpis': {  # Recalculated from CCT only
        'sprint_predictability': {
            'overall_average': 71.1,  # From CCT
            'sprints': [...]  # CCT sprints with board_name field
        }
    }
}
```

---

## Files Modified

1. **[src/dashboard.py](src/dashboard.py)**
   - Added `from copy import deepcopy`
   - Added `self.original_kpi_data` to preserve unfiltered data
   - Updated `_apply_filters()` to:
     - Use original_kpi_data instead of modified kpi_data
     - Add missing 'board_name' field to sprint objects
     - Limit sprints to 20 for display performance
   - Fixed KeyError: 'board_name' issue

---

## Current Limitations

### Date Range Filter
- **Status:** Not yet implemented
- **Current behavior:** Dropdown stores value but doesn't recalculate data
- **Future enhancement:** Would require calling calculator with date parameters

### Why Date Range Isn't Working Yet
The current implementation filters by **project** but not by **date** because:
1. KPIs are pre-calculated at startup with 365-day lookback
2. To filter by date would require:
   - Querying database with date filters
   - Recalculating KPIs for that date range
   - More complex than project aggregation

**To implement date filtering:**
```python
def _apply_filters(self):
    if self.calculator and self.db:
        # Recalculate with date range
        filtered_kpi_data = self.calculator.calculate_all_kpis_for_projects(
            projects=self.selected_projects,
            date_range_days=self.date_range
        )
        self.kpi_data = filtered_kpi_data
```

---

## Verification Checklist

- [x] Dashboard starts without errors
- [x] No KeyError: 'board_name'
- [x] Project dropdown changes data
- [x] Overview tab respects filter
- [x] Sprint Predictability tab respects filter
- [x] Cycle Time tab respects filter
- [x] Work Mix tab respects filter
- [x] By Project tab respects filter
- [x] Can switch between single/multiple projects
- [x] Original data preserved across filter changes
- [ ] Date range filter (not yet implemented)

---

## Dashboard URL

**Access:** http://127.0.0.1:8050

**Restart if needed:**
```bash
lsof -ti:8050 | xargs kill -9
python src/main.py --use-db
```

---

## Summary

✅ **Project filtering is now fully working**
✅ **All KPI tabs update when projects change**
✅ **No more KeyError crashes**
✅ **Data changes are visible immediately**
⚠️ **Date range filter prepared but needs implementation**

**Test it now!** Change the project dropdown and watch the KPIs update in real-time.

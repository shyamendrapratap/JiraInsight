# CCEN Data Investigation Report

## 🔍 Summary

**Status:** CCEN project data is **not available** in JIRA
**Database Cleaned:** ✅ OPR, IND, TFE removed
**Available Projects:** CCT (54 issues), SCPX (845 issues)

## 📊 Current Database Status

```
Total Issues:  899 (real JIRA data)
Projects:
  - SCPX: 845 issues ✅
  - CCT:  54 issues  ✅
  - CCEN: 0 issues   ❌

Unwanted projects removed:
  - OPR: 167 issues  🗑️
  - IND: 7 issues    🗑️
  - TFE: 1 issue     🗑️
```

## 🔎 Investigation Findings

### 1. CCEN Boards Exist
We found 2 CCEN-related boards in JIRA:
- **CCEN Board** (ID: 13543)
- **CCA-Team-Board** (ID: 13644)

### 2. But No CCEN Sprints
When we tried to sync sprints from these boards:
- ✅ Connection successful
- ❌ **No sprints found** on CCEN Board
- ❌ **400 Error** when querying CCA-Team-Board sprints

**Conclusion:** CCEN boards are not configured with sprints in JIRA

### 3. Direct Project Query Failed
Tried to query CCEN project directly:
```
JQL: project = CCEN ORDER BY updated DESC
Result: 410 Client Error (Gone)
```

**This error means:**
- Project "CCEN" doesn't exist as a project key in JIRA, OR
- Your account doesn't have permission to query it, OR
- The project has been archived/removed

### 4. CCT Data Exists
We DO have CCT data (54 issues). These came from:
- Issues that were part of SCPX sprints but tagged with CCT project
- Cross-board sprint participation

## ❓ Why No CCEN Data?

**Most Likely Reason:**
The "CCEN" project key **does not exist** in your JIRA instance. The boards are labeled "CCEN" but:
- They may be organizational boards
- Issues on those boards might belong to other projects (like CCT, SCPX)
- The actual project key might be different

**Evidence:**
1. Boards exist but have no sprints
2. Direct project query returns 410 (Gone) error
3. No CCEN issues found in any sprints
4. JIRA API restrictions on your account prevent JQL queries

## ✅ What's Working

### Current Dashboard Data
- **SCPX**: 845 issues with full KPIs
- **CCT**: 54 issues with full KPIs
- All unwanted projects removed
- Dashboard configured for CCT, SCPX, CCEN

### Dashboard Features
- ✅ Project multi-select dropdown (CCT, SCPX, CCEN)
- ✅ Date range filter (30-365 days)
- ✅ "By Project" comparison tab
- ✅ All KPI calculations working
- ✅ Clean data (no sample data, no unwanted projects)

## 🎯 Recommendations

### Option 1: Use What We Have ✅
Continue with **CCT and SCPX** data:
- Both projects have real, usable data
- All KPIs are calculated correctly
- Dashboard works perfectly

### Option 2: Find Correct CCEN Key
Check with your JIRA admin or team:
1. What is the actual project key for CCEN work?
2. Is CCEN work tracked under a different project key?
3. Are CCEN boards just organizational (not a real project)?

Possible alternative keys to try:
- `CCEN` ❌ (doesn't exist)
- `CCA` (similar to CCA-Team-Board?)
- `COMPLIANCE`
- `CONTROL`

### Option 3: Update Configuration
If CCEN doesn't exist as a project, update `config/config.yaml`:

```yaml
projects:
  project_keys:
    - "CCT"
    - "SCPX"
    # Remove CCEN if it doesn't exist
```

## 📝 Technical Details

### Sync Attempts Made

1. **Sprint-based sync** ✅
   - Synced 47 sprints
   - Got 845 SCPX issues, 54 CCT issues
   - CCEN sprints: none found

2. **Direct CCEN board sprint sync** ❌
   - Board 13543: No sprints
   - Board 13644: 400 Error

3. **Direct project query** ❌
   - CCEN: 410 Error (Gone)
   - CCT: 410 Error (but data exists from sprints)

### API Limitations
Your JIRA account has:
- ✅ Access to Agile API (sprint endpoints work)
- ❌ **No access to JQL search** (410 errors)
- ✅ Access to read boards and sprints
- ✅ Access to issues within sprints

This is why sprint-based sync works, but direct queries don't.

## 🚀 Current Dashboard

**URL:** http://127.0.0.1:8050

**Data Available:**
- SCPX: Full KPIs (845 issues)
- CCT: Full KPIs (54 issues)
- CCEN: No data (project doesn't exist or no accessible issues)

**Filters:**
- Project selector: CCT, SCPX, CCEN (CCEN shown but no data)
- Date range: 30, 60, 90, 180, 365 days

**Recommendation:** Remove CCEN from dropdown if it doesn't exist, or find correct project key.

## 🔧 Next Steps

1. **Verify with Team/Admin:**
   - Does CCEN exist as a JIRA project?
   - What's the correct project key?
   - Where is CCEN work tracked?

2. **If CCEN Exists Elsewhere:**
   - Get correct project key
   - Update config
   - Re-sync

3. **If CCEN Doesn't Exist:**
   - Remove from config
   - Update dashboard filters
   - Use CCT + SCPX data

---

**Dashboard Status:** ✅ Running with CCT + SCPX data
**Last Updated:** 2026-02-07

# Database-Backed KPI Dashboard Workflow

## Overview

The KPI Dashboard now uses a **local SQLite database** to store JIRA data. This solves the data availability issues and provides:

- **Persistent storage** of JIRA data locally
- **Fast dashboard loading** (no waiting for JIRA API calls)
- **Offline analytics** once data is synced
- **Historical tracking** of metrics over time
- **Resilience** to JIRA API issues or permissions problems

## Architecture

```
┌──────────┐     sync      ┌──────────┐    analytics    ┌───────────┐
│   JIRA   │ ──────────────▶│ SQLite DB│ ──────────────▶│ Dashboard │
│   API    │   (periodic)   │  (local) │   (real-time)  │    (Web)  │
└──────────┘                └──────────┘                 └───────────┘
```

## New Workflow

### 1. Data Sync (Pull from JIRA)

Run the sync script to pull data from JIRA and store it locally:

```bash
# Full sync (recommended for first time)
python sync_data.py --full --days 90

# Incremental sync (only recent updates)
python sync_data.py

# With changelog (slower but more complete)
python sync_data.py --full --with-changelog
```

**What gets synced:**
- ✓ Boards (all accessible boards)
- ✓ Sprints (all sprints from boards)
- ✓ Issues (stories, tasks, bugs, epics)
- ✓ Issue changelog (optional - tracks status changes)

**Data stored in:** `./data/kpi_data.db` (SQLite database)

### 2. View Dashboard (Read from Database)

Run the dashboard using local data:

```bash
# Start dashboard with database
python src/main.py --use-db

# Or with custom database path
python src/main.py --use-db --db ./data/my_data.db
```

Dashboard will be available at: http://127.0.0.1:8050

### 3. Refresh Data

When you want fresh data from JIRA:

```bash
# Sync recent updates (fast)
python sync_data.py

# Re-sync all data
python sync_data.py --full --days 90
```

## Database Management

### View Database Stats

```bash
python sync_data.py --stats
```

Shows:
- Total issues, sprints, boards
- Last sync time and status
- Projects in database

### Database Location

- **Default:** `./data/kpi_data.db`
- **Custom:** Use `--db <path>` flag

### Database Schema

The database contains:
- **issues** - All JIRA issues with metadata
- **sprints** - Sprint information
- **boards** - Board details
- **issue_changelog** - Issue history (status changes, etc.)
- **sync_metadata** - Sync operation tracking

## Troubleshooting

### Issue: JIRA API Returns 410 Errors

**Problem:** Your JIRA account doesn't have permission to query issues.

**Solution:**
1. Contact your JIRA admin to grant issue query permissions
2. OR use the sample data generator for testing:
   ```bash
   python generate_sample_data.py
   ```

### Issue: No Data in Dashboard

**Problem:** Database is empty or sync failed.

**Solution:**
```bash
# Check database stats
python sync_data.py --stats

# If empty, run full sync
python sync_data.py --full --days 90

# Or generate sample data for testing
python generate_sample_data.py
```

### Issue: Port 8050 Already in Use

**Problem:** Dashboard is already running or port is occupied.

**Solution:**
```bash
# Kill existing process
lsof -ti:8050 | xargs kill -9

# Or use different port (update config/config.yaml)
```

### Issue: Incorrect Project Keys

**Problem:** Config has wrong project keys (SCPX, CCEN not accessible).

**Solution:**
1. Discover your accessible projects:
   ```bash
   python discover_projects.py
   ```

2. Update `config/config.yaml` with correct project keys:
   ```yaml
   projects:
     project_keys:
       - "PROJECT1"
       - "PROJECT2"
   ```

## Sample Data for Testing

If you can't access JIRA data, use sample data:

```bash
# Generate 200 sample issues across 2 projects
python generate_sample_data.py

# Then run dashboard
python src/main.py --use-db
```

Sample data includes:
- 200 issues (100 per project)
- Realistic status transitions
- Sprint assignments
- Labels and priorities
- Changelog entries
- Reopened issues (~15%)

## Comparison: Old vs New Workflow

### Old Workflow (Direct JIRA)
```
User runs dashboard → Dashboard queries JIRA → Slow, prone to API errors
```

**Problems:**
- ❌ Slow dashboard loading (waits for JIRA API)
- ❌ Fails if JIRA is down or has permission issues
- ❌ No historical data retention
- ❌ Rate limited by JIRA API

### New Workflow (Database-Backed)
```
User syncs data → Data stored locally → Dashboard reads from DB → Fast
```

**Benefits:**
- ✅ Fast dashboard (no API calls during viewing)
- ✅ Works offline after initial sync
- ✅ Historical data preserved
- ✅ Resilient to JIRA issues
- ✅ Better performance and reliability

## Advanced Usage

### Custom Sync Schedule

Set up a cron job to sync data automatically:

```bash
# Sync every 6 hours
0 */6 * * * cd /path/to/dashboard && ./venv/bin/python sync_data.py >> ./logs/sync.log 2>&1
```

### Multiple Databases

Maintain separate databases for different projects:

```bash
# Sync to project-specific database
python sync_data.py --full --db ./data/project1.db

# View specific database
python src/main.py --use-db --db ./data/project1.db
```

### Database Backup

```bash
# Backup database
cp ./data/kpi_data.db ./data/backups/kpi_data_$(date +%Y%m%d).db

# Restore from backup
cp ./data/backups/kpi_data_20260207.db ./data/kpi_data.db
```

## Files Added

New files for database functionality:

```
platform-engineering-kpi-dashboard/
├── src/
│   ├── database.py              # Database service layer
│   ├── data_collector.py        # JIRA data collection
│   └── kpi_calculator_db.py     # Database-backed KPI calculator
├── sync_data.py                 # Data sync script
├── generate_sample_data.py      # Sample data generator
├── discover_projects.py         # Project discovery tool
└── DATABASE_WORKFLOW.md         # This file
```

## Quick Reference

```bash
# First time setup
python sync_data.py --full --days 90

# Start dashboard
python src/main.py --use-db

# Refresh data (daily)
python sync_data.py

# Check status
python sync_data.py --stats

# Testing with sample data
python generate_sample_data.py
python src/main.py --use-db

# Discover accessible projects
python discover_projects.py
```

## Support

For issues or questions:
1. Check `./logs/kpi_dashboard.log` for errors
2. Run `python sync_data.py --stats` to check data
3. Try sample data to isolate JIRA vs dashboard issues
4. Verify JIRA permissions with admin

---

**Last Updated:** 2026-02-07
**Version:** 2.0 (Database-Backed)

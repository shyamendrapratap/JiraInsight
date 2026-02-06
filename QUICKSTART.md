# Quick Start Guide

Get your Platform Engineering KPI Dashboard running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- JIRA account with API access
- JIRA API Token ([generate here](https://id.atlassian.com/manage-profile/security/api-tokens))

## Installation

### Option 1: Automated Setup (Recommended)

```bash
# 1. Navigate to project directory
cd platform-engineering-kpi-dashboard

# 2. Run setup script
./setup.sh

# 3. Edit .env file with your JIRA credentials
nano .env  # or use your preferred editor
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env

# 4. Edit .env with your credentials
nano .env
```

## Configuration

### Step 1: Set Up JIRA Credentials

Edit `.env` file:

```env
JIRA_API_TOKEN=your_actual_token_here
JIRA_EMAIL=your.email@company.com
JIRA_URL=https://your-company.atlassian.net
```

**How to get JIRA API Token:**
1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token to `.env` file

### Step 2: Configure Projects

Edit `config/config.yaml`:

```yaml
projects:
  project_keys:
    - "PLATFORM"    # Replace with your actual project keys
    - "INFRA"
    - "DEVOPS"
```

## Test Connection

```bash
python src/main.py --test-connection
```

Expected output:
```
============================================================
Testing JIRA Connection...
============================================================
Connected to JIRA as: Your Name
✓ JIRA connection successful!
```

## Run Dashboard

```bash
python src/main.py
```

Open your browser and navigate to: http://127.0.0.1:8050

## Common Issues & Solutions

### Issue: "Configuration validation failed: Missing JIRA API token"

**Solution:** Edit `.env` file and add your actual JIRA API token.

---

### Issue: "JIRA connection failed"

**Solutions:**
1. Verify JIRA URL is correct (must start with https://)
2. Check API token is valid (tokens don't expire by default)
3. Ensure email matches your JIRA account
4. Check network/firewall settings

---

### Issue: "No data available" in dashboard

**Solutions:**
1. Verify project keys exist in JIRA
2. Check you have read permissions for these projects
3. Ensure projects have sprints and issues
4. Review logs: `cat logs/kpi_dashboard.log`

---

### Issue: "Module not found" errors

**Solution:** Activate virtual environment:
```bash
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

## Next Steps

### 1. Add Required Labels to JIRA

Add these labels to your JIRA Epics and Stories:

- `feature_dev` - Feature development
- `tech_debt` - Technical debt
- `reliability_perf` - Reliability & performance
- `ops_enablement` - Ops enablement
- `unplanned` - Unplanned/interrupt work

### 2. Configure Label Your Epics

Apply appropriate labels to existing Epics. Stories will inherit these labels.

### 3. Run Data Collection

```bash
# Collect data and save to file
python src/main.py --collect-only --output data/initial_data.json

# View summary
python src/main.py --load-data data/initial_data.json --summary
```

### 4. Start Dashboard

```bash
python src/main.py
```

## Advanced Usage

### Collect and Save Data Without Dashboard

```bash
python src/main.py --collect-only --output data/kpi_data.json
```

### Load Previously Collected Data

```bash
python src/main.py --load-data data/kpi_data.json
```

### Print Summary to Console

```bash
python src/main.py --summary
```

### Combine Options

```bash
# Collect, save, and show summary without dashboard
python src/main.py --collect-only --output data/data.json --summary
```

## Customization

### Change Dashboard Port

Edit `config/config.yaml`:

```yaml
dashboard:
  port: 9000  # Change from default 8050
  host: "127.0.0.1"
```

Or use environment variable:

```bash
DASHBOARD_PORT=9000 python src/main.py
```

### Adjust Analysis Period

Edit `config/config.yaml`:

```yaml
kpis:
  analysis_periods:
    sprint_lookback: 5     # Analyze last 5 sprints (default: 3)
    rolling_days: [30, 60, 90]  # Rolling periods
```

### Configure Thresholds

Edit `config/config.yaml`:

```yaml
kpis:
  sprint_predictability:
    threshold_warning: 70   # Warn if below 70%
    threshold_critical: 50  # Critical if below 50%
```

## Dashboard Features

### Navigation

- **Overview Tab** - Summary of all KPIs
- **Individual KPI Tabs** - Detailed view for each metric
- **JQL Queries Tab** - All queries used for transparency

### Exporting Data

Data is automatically saved when collected. Files are in: `data/exports/`

### Refreshing Data

Stop dashboard (CTRL+C) and restart to fetch fresh data.

## Scheduled Data Collection

### Linux/Mac (cron)

```bash
# Edit crontab
crontab -e

# Add line to collect data daily at 9 AM
0 9 * * * cd /path/to/project && /path/to/venv/bin/python src/main.py --collect-only --output data/daily_$(date +\%Y\%m\%d).json
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Action: Start a program
4. Program: `C:\path\to\venv\Scripts\python.exe`
5. Arguments: `src/main.py --collect-only --output data/daily.json`
6. Start in: `C:\path\to\project`

## Getting Help

### Check Logs

```bash
tail -f logs/kpi_dashboard.log
```

### Verbose Logging

Edit `config/config.yaml`:

```yaml
logging:
  level: "DEBUG"  # Change from INFO to DEBUG
```

### Test Individual Components

```python
# Test JIRA connection
python src/main.py --test-connection

# Collect data only (no dashboard)
python src/main.py --collect-only

# Load and view data
python src/main.py --load-data data/file.json --summary
```

## Deactivating Virtual Environment

```bash
deactivate
```

## Stopping the Dashboard

Press `CTRL+C` in the terminal running the dashboard.

## Complete Example Workflow

```bash
# 1. Setup
./setup.sh

# 2. Configure credentials
nano .env

# 3. Configure projects
nano config/config.yaml

# 4. Test connection
python src/main.py --test-connection

# 5. Collect initial data
python src/main.py --collect-only --output data/initial.json

# 6. View summary
python src/main.py --load-data data/initial.json --summary

# 7. Run dashboard
python src/main.py
```

## What to Expect

### First Run
- Data collection may take 2-10 minutes depending on project size
- Dashboard will show all 6 KPIs with visualizations
- JQL queries are available in the dashboard for reference

### Typical Data
- Sprint Predictability: 60-80% is common
- Story Spillover: <20% is good
- Cycle Time: 5-15 days is typical
- Work Mix: Should show realistic distribution
- Unplanned Work: <20% is ideal
- Reopened Stories: <10% is good

## Resources

- **Full Documentation**: [README.md](README.md)
- **JQL Reference**: [JQL_REFERENCE.md](JQL_REFERENCE.md)
- **Configuration**: [config/config.yaml](config/config.yaml)

---

**Need Help?**

Check logs: `logs/kpi_dashboard.log`
Review config: `config/config.yaml`
Test connection: `python src/main.py --test-connection`

---

**Quick Start Guide v1.0**
*Get started in 5 minutes!*

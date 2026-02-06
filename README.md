# Platform Engineering KPI Dashboard

A comprehensive, leadership-focused KPI dashboard for Platform Engineering teams using JIRA data. This project provides actionable insights into team performance, delivery predictability, and work distribution without exposing individual engineers or creating fear.

## 🎯 Purpose

Improve delivery predictability, execution hygiene, and work clarity by tracking:
- **Sprint Predictability** - Planning accuracy & scope discipline
- **Story Spillover** - Story slicing & ambiguity management
- **Cycle Time** - Flow efficiency
- **Work Mix Distribution** - Where engineering capacity is going
- **Unplanned Work Load** - Interrupt pressure & planning realism
- **Reopened Stories** - Definition of Done & clarity

## 🏗️ Design Principles

- **Team-level metrics only** (monthly trends)
- **Trend-based signals, not scorecards**
- **Minimal labels** (≤5 total)
- **JIRA as intent & planning signal**
- **Metrics drive conversations, not judgments**

## 📋 Prerequisites

- Python 3.8 or higher
- JIRA account with API access
- JIRA API Token (generate at: https://id.atlassian.com/manage-profile/security/api-tokens)
- Access to JIRA projects (read permissions required)

## 🚀 Quick Start

### 1. Clone or Download the Project

```bash
cd platform-engineering-kpi-dashboard
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or using virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure JIRA Connection

#### Option A: Using Configuration File

Edit `config/config.yaml`:

```yaml
jira:
  urls:
    - "https://your-company.atlassian.net"
  token: "YOUR_JIRA_API_TOKEN"
  email: "your.email@company.com"

projects:
  project_keys:
    - "PLATFORM"
    - "INFRA"
    - "DEVOPS"
```

#### Option B: Using Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env`:

```env
JIRA_API_TOKEN=your_jira_api_token_here
JIRA_EMAIL=your.email@company.com
JIRA_URL=https://your-company.atlassian.net
```

### 4. Test JIRA Connection

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

### 5. Run the Dashboard

```bash
python src/main.py
```

The dashboard will be available at: http://127.0.0.1:8050

## 📊 KPI Descriptions

### KPI 1: Sprint Predictability
**What it tells us:** Planning accuracy & scope discipline

**Metric:** % of committed stories completed within sprint

**EM Action Required:**
- Ensure sprint commitments are not inflated
- Avoid mid-sprint scope injection without `unplanned` label

**JQL Example:**
```jql
sprint = 123 AND statusCategory = Done AND type in (Story, Task, Bug)
```

---

### KPI 2: Story Spillover
**What it tells us:** Story slicing & ambiguity management

**Metric:** % of stories spanning more than 2 sprints

**EM Action Required:**
- Break work vertically
- Use spikes explicitly instead of oversized stories

**JQL Example:**
```jql
sprint in closedSprints() AND type in (Story, Task)
```
*Note: Requires post-processing to count sprints per issue*

---

### KPI 3: Average Story Cycle Time
**What it tells us:** Flow efficiency

**Metric:** Avg time from "In Progress" → "Done"

**EM Action Required:**
- Reduce WIP
- Identify recurring blockers early

**JQL Example:**
```jql
statusCategory = Done AND type in (Story, Task) AND resolved >= -90d
```
*Note: Requires changelog analysis for precise cycle time*

---

### KPI 4: Work Mix Distribution
**What it tells us:** Where engineering capacity is going

**Metric:** % Feature vs Tech Debt vs Reliability vs Ops

**EM Action Required:**
- Ensure Epics are labeled correctly
- Highlight invisible ops/enablement load

**JQL Examples:**
```jql
# Feature Development
type in (Epic, Story, Task) AND labels = feature_dev AND created >= -90d

# Tech Debt
type in (Epic, Story, Task) AND labels = tech_debt AND created >= -90d

# Reliability & Performance
type in (Epic, Story, Task) AND labels = reliability_perf AND created >= -90d

# Ops Enablement
type in (Epic, Story, Task) AND labels = ops_enablement AND created >= -90d

# Unplanned Work
type in (Epic, Story, Task) AND labels = unplanned AND created >= -90d
```

---

### KPI 5: Unplanned Work Load
**What it tells us:** Interrupt pressure & planning realism

**Metric:** % of stories labeled `unplanned` per sprint

**EM Action Required:**
- Tag interrupt work explicitly
- Use this data to negotiate roadmap realism

**JQL Example:**
```jql
sprint = 123 AND labels = unplanned AND type in (Story, Task, Bug)
```

---

### KPI 6: Reopened Stories
**What it tells us:** Definition of Done & clarity

**Metric:** % of issues reopened after Done

**EM Action Required:**
- Tighten acceptance criteria
- Improve review & validation

**JQL Examples:**
```jql
# Query 1: Issues that were Done but are now NOT Done
status WAS IN (Done, Closed, Resolved) AND statusCategory != Done AND type in (Story, Task, Bug) AND updated >= -90d

# Query 2: Issues where status changed FROM Done
status CHANGED FROM Done AND type in (Story, Task, Bug) AND updated >= -90d
```

## 🏷️ JIRA Labels (OPTIONAL - Configurable per Space/Project)

**⚠️ Labels are OPTIONAL!** You only need them if you want to track:
- **KPI 4: Work Mix Distribution** - What % of work is features vs tech debt vs reliability, etc.
- **KPI 5: Unplanned Work** - Track interrupt/unplanned work explicitly

**All other KPIs work WITHOUT labels:**
- ✅ KPI 1: Sprint Predictability - Works with JIRA projects only
- ✅ KPI 2: Story Spillover - Works with JIRA projects only
- ✅ KPI 3: Cycle Time - Works with JIRA projects only
- ✅ KPI 6: Reopened Stories - Works with JIRA projects only

---

### If You Want to Use Labels

The dashboard supports **two labeling approaches**:

### Option 1: Global Labels (Same labels for all projects)

Apply these labels to **Epics and Stories**:

| Label | Purpose |
|-------|---------|
| `feature_dev` | Product / feature development |
| `tech_debt` | Refactors, cleanup, stability work |
| `reliability_perf` | Scale, performance, DR, resiliency |
| `ops_enablement` | Docs, follow-ups, enablement, migrations |
| `unplanned` | Interrupt / ad-hoc work |

### Option 2: Space-Specific Labels (Different labels per JIRA space/project)

Configure custom labels for each JIRA space in `config/config.yaml`:

**Example - Platform Engineering space:**
- `feature`, `tech-debt`, `performance`, `ops`, `interrupt`

**Example - Infrastructure space:**
- `infra-feature`, `infra-maintenance`, `security`, `compliance`, `incident`

**Example - DevOps space:**
- `automation`, `tooling`, `monitoring`, `support`, `urgent`

### Configuration

Edit `config/config.yaml` to choose your approach:

```yaml
labels:
  # Option 1: Use global labels (enabled: true)
  global:
    enabled: true
    work_categories:
      - label: "feature_dev"
        name: "Feature Development"
        description: "Product development"

  # Option 2: Define space-specific labels
  spaces:
    - name: "Platform Engineering"
      projects: ["PLATFORM", "PLATFORM-API"]
      work_categories:
        - label: "feature"
          name: "Feature Work"
          description: "New features"
```

**Important:** Use the "Labels" field in JIRA. Stories should inherit labels from their parent Epic.

## 🔧 Usage

### Basic Usage

Run dashboard with live data collection:
```bash
python src/main.py
```

### Advanced Usage

#### Collect data and save to file (without starting dashboard):
```bash
python src/main.py --collect-only --output data/my_kpi_data.json
```

#### Load previously collected data:
```bash
python src/main.py --load-data data/my_kpi_data.json
```

#### Print KPI summary to console:
```bash
python src/main.py --summary
```

#### Combine options:
```bash
# Collect, save, show summary, but don't start dashboard
python src/main.py --collect-only --output data/kpi_$(date +%Y%m%d).json --summary
```

## 📁 Project Structure

```
platform-engineering-kpi-dashboard/
├── config/
│   └── config.yaml              # Main configuration file
├── src/
│   ├── main.py                  # Main application entry point
│   ├── config_loader.py         # Configuration loader
│   ├── jira_client.py           # JIRA API client
│   ├── kpi_calculator.py        # KPI calculation logic with JQL queries
│   └── dashboard.py             # Dashboard visualization (Plotly Dash)
├── data/
│   ├── cache/                   # Cache directory (auto-created)
│   └── exports/                 # Exported data (auto-created)
├── logs/
│   └── kpi_dashboard.log        # Application logs (auto-created)
├── .env.example                 # Environment variables template
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## ⚙️ Configuration Reference

### JIRA Configuration

```yaml
jira:
  urls:
    - "https://jira1.atlassian.net"
    - "https://jira2.company.com"  # Multiple JIRA instances supported
  token: "YOUR_API_TOKEN"
  email: "your.email@company.com"
```

### Projects Configuration

```yaml
projects:
  project_keys:
    - "PLATFORM"
    - "INFRA"

  # Optional: Team mapping
  teams:
    - name: "Platform Team A"
      projects: ["PLATFORM"]
    - name: "Infrastructure Team"
      projects: ["INFRA"]
```

### KPI Configuration

```yaml
kpis:
  analysis_periods:
    sprint_lookback: 3          # Number of closed sprints to analyze
    rolling_days: [30, 60, 90]  # Rolling period in days

  sprint_predictability:
    enabled: true
    threshold_warning: 70       # Warn if below 70%
    threshold_critical: 50      # Critical if below 50%

  # ... (see config/config.yaml for all options)
```

### Dashboard Configuration

```yaml
dashboard:
  title: "Platform Engineering KPI Dashboard"
  port: 8050
  host: "127.0.0.1"  # localhost only (leadership access)
  debug: false
```

## 🔒 Security Notes

1. **Never commit sensitive data:**
   - Add `.env` to `.gitignore`
   - Use environment variables for tokens
   - Keep API tokens secure

2. **Access Control:**
   - Dashboard runs on localhost by default (127.0.0.1)
   - For remote access, use SSH tunneling or VPN
   - Consider adding authentication layer for production

3. **JIRA Permissions:**
   - Requires read-only access to JIRA projects
   - No project admin rights needed
   - Uses standard JIRA API

## 📈 Dashboard Features

- **Interactive Visualizations:** Charts, graphs, and tables
- **Multi-tab Interface:** Separate views for each KPI
- **JQL Query Reference:** All queries used for each KPI
- **Export Functionality:** Save KPI data as JSON
- **Responsive Design:** Bootstrap-based UI
- **Real-time Data:** Fetch latest data from JIRA

## 🎨 Dashboard Tabs

1. **Overview** - Summary of all KPIs with key metrics
2. **Sprint Predictability** - Completion rates by sprint
3. **Story Spillover** - Issues spanning multiple sprints
4. **Cycle Time** - Time from In Progress to Done
5. **Work Mix** - Distribution of work by category
6. **Unplanned Work** - Interrupt work tracking
7. **Reopened Stories** - Quality and clarity metrics
8. **JQL Queries** - All queries used for transparency

## 🚫 What's Explicitly OUT of Scope

This dashboard **intentionally excludes**:
- Individual performance metrics
- Commit counts, story points per person
- Time tracking or activity measures
- Any ranking across teams

**This dashboard is diagnostic, not evaluative.**

## 🤝 Process Changes Required from EMs

| Change | Owner |
|--------|-------|
| Ensure every Epic has 1 label | EM |
| Stories inherit Epic label | Team |
| Tag unplanned work explicitly | EM |
| Avoid ad-hoc labels | EM |
| Accept trends matter more than sprint noise | Leadership |

**No workflow changes. No admin permissions needed.**

## 📅 Rollout Plan

### Week 0 (Alignment – 2-3 days)
- Review labels & KPIs with leadership
- Lock interpretation guardrails

### Week 1 (Setup)
- Create global JIRA filters across projects
- Build leadership-only dashboard
- Dry-run metrics on historical data

### Week 2 (Pilot)
- Run dashboard with 2-3 EMs
- Validate signal vs noise
- Refine language & framing

### Week 3 (Rollout)
- Start monthly EM reviews
- Set quarterly deep-dive cadence

## 💡 How This Will Be Used

> "We will use this dashboard to identify where teams need help, not where people are failing. Any metric without EM context is considered invalid."

## 🐛 Troubleshooting

### Connection Issues

**Problem:** `JIRA connection failed`

**Solution:**
1. Verify JIRA URL is correct (include https://)
2. Check API token is valid
3. Ensure email matches JIRA account
4. Test connection: `python src/main.py --test-connection`

### No Data Returned

**Problem:** Dashboard shows "No data available"

**Solution:**
1. Verify project keys exist in JIRA
2. Check you have read permissions
3. Ensure projects have sprints and issues
4. Review logs in `logs/kpi_dashboard.log`

### Missing Sprint Data

**Problem:** Sprint Predictability shows no sprints

**Solution:**
1. Verify boards are configured in JIRA
2. Check projects use Scrum/Kanban boards
3. Ensure sprints are closed (not active)

### Label Issues

**Problem:** Work Mix shows all "unlabeled"

**Solution:**
1. Add required labels to JIRA (see Labels section)
2. Apply labels to Epics and Stories
3. Re-run data collection

## 📊 Sample Output

```
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

⚠️  Unplanned Work: 8.3%
   Sprints analyzed: 9

🔄 Reopened Stories: 6.2%
   Reopened: 4 / 65

============================================================
```

## 🔄 Updates & Maintenance

### Refreshing Data

Data is automatically fetched when the dashboard starts. To refresh:
1. Stop the dashboard (CTRL+C)
2. Restart: `python src/main.py`

### Scheduling Automated Reports

Use cron (Linux/Mac) or Task Scheduler (Windows) to collect data regularly:

```bash
# Cron example: Collect data daily at 9 AM
0 9 * * * cd /path/to/project && /path/to/venv/bin/python src/main.py --collect-only --output data/daily_$(date +\%Y\%m\%d).json
```

## 📞 Support & Feedback

For issues, questions, or feature requests:
1. Check logs: `logs/kpi_dashboard.log`
2. Review configuration: `config/config.yaml`
3. Test connection: `python src/main.py --test-connection`

## 📜 License

This project is provided as-is for internal use.

## 🙏 Final Recommendation

- **Start team-level only**
- **Build trust through consistency & restraint**
- **Introduce individual signals only if patterns persist**
- **Protect high performers by making invisible work visible**

---

**Platform Engineering KPI Dashboard v1.0**
*Making invisible work visible through data-driven conversations*

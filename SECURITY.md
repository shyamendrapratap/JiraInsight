# Security & Credential Management

## 🔒 Important: Protect Your Credentials

This project requires JIRA API credentials to function. **NEVER commit real credentials to version control.**

---

## Setup Instructions

### 1. Create Your `.env` File

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

### 2. Get Your JIRA API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **"Create API token"**
3. Give it a name (e.g., "KPI Dashboard")
4. Copy the generated token
5. Paste it into your `.env` file as `JIRA_API_TOKEN`

### 3. Configure Your Environment Variables

Edit `.env` with your actual values:

```env
JIRA_API_TOKEN=your_actual_token_here
JIRA_EMAIL=your.email@company.com
JIRA_URL=https://your-company.atlassian.net
```

### 4. Verify `.env` is Ignored

Check that your `.env` file will NOT be committed:

```bash
git status
```

You should **NOT** see `.env` in the list of files to commit. If you do, stop and check your `.gitignore` file.

---

## What's Protected

The following files are **automatically ignored** by `.gitignore`:

- `.env` - Your actual credentials
- `logs/*.log` - May contain API request details
- `data/*.db` - May contain cached JIRA data
- `data/cache/` - Temporary API response cache

---

## What's Safe to Commit

These files contain **only placeholders** and are safe to commit:

- `.env.example` - Template with no real credentials
- `config/config.yaml` - Configuration with placeholder values
- All source code in `src/`
- Documentation files

---

## Before Pushing to GitHub

1. **Double-check** `.env` is ignored:
   ```bash
   git status | grep ".env"
   ```
   Should return nothing (or only `.env.example`)

2. **Search for credentials** in tracked files:
   ```bash
   git grep -i "ATATT3x"  # JIRA token pattern
   git grep -i "@company.com"  # Your email
   git grep -i "atlassian.net"  # JIRA URL
   ```
   Should return NO matches in source code

3. **Review what you're committing**:
   ```bash
   git diff --cached
   ```

---

## Credential Rotation

If you accidentally commit credentials:

1. **Immediately revoke** the exposed API token at:
   https://id.atlassian.com/manage-profile/security/api-tokens

2. **Generate a new token** and update your `.env` file

3. **Remove the credential from git history**:
   ```bash
   # Use git-filter-repo or BFG Repo Cleaner
   # Or create a fresh clone without history
   ```

4. **Force push** (if necessary) to overwrite remote history

---

## Questions?

If you're unsure whether something contains credentials, **don't commit it**. Ask your team first.

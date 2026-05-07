# Workflow OS — Automation Layer

Replaces Google Apps Script with **cron + Google Workspace CLI**.

## Components

### `drive_poller.py` — EOD Folder Watcher
Polls Google Drive folder `1oTfpoAddnGArr6M2bLojsYtRc7_Hd7QM` every 15 minutes.
Detects new/changed EOD docs → sends to FastAPI webhook.

**Auth options:**
- `gcloud auth application-default login` (preferred — uses your Google account)
- `GOOGLE_API_KEY` env var (fallback)

**Run:** `python3 drive_poller.py`
**Cron:** Registered in OpenClaw as "EOD Drive Poller" every 15min

### `github_issues_bot.py` — Infra Event → GitHub Issue
Called by the FastAPI dispatcher for `infra_event` items.
Auto-creates labelled GitHub issues with Claude root cause hypothesis.
Deduplication: same service+error_type twice in 24h = P0 escalation.

**Env vars needed:**
- `GITHUB_TOKEN` = `github_pat_11B74W7FY0...d2OM`
- `GITHUB_REPO` = `mnjbold/workflow-os`

## Setup

```bash
# 1. Authenticate with Google (one-time)
/data/google-cloud-sdk/bin/gcloud auth application-default login --no-browser

# 2. Set env vars
export WORKFLOW_OS_WEBHOOK_URL=https://your-railway-app.up.railway.app/webhook/eod
export GITHUB_TOKEN=<your-github-pat>
export GITHUB_REPO=mnjbold/workflow-os

# 3. Test the poller manually
python3 automation/drive_poller.py

# 4. Test the GitHub bot
python3 automation/github_issues_bot.py
```

## OpenClaw Cron (already registered)
- `PM EOD Drive Poller` — every 15 min, calls drive_poller.py
- `PM Daily Standup` — 9am MYT weekdays
- `PM Daily Risk Check` — 10am MYT daily
- `PM EOD Summary` — 6pm MYT weekdays
- `PM Weekly Summary` — 4:30pm MYT Fridays
- `PM Backlog Grooming` — 5pm MYT Fridays
- `PM Metrics Update` — midnight MYT daily
- `PM Sprint Planning` — 8:30am MYT Mondays

# Workflow OS Deployment Guide

## Overview

Workflow OS is now deployed and ready for configuration. The system monitors a Google Drive folder for new EOD (End-of-Day) reports and automatically processes them into tasks and workflows.

## Repository

- **GitHub**: https://github.com/mnjbold/workflow-os
- **Branch**: master
- **Local Path**: `/data/.openclaw/.openclaw/workspace/workflow-os`

## Architecture

```
┌─────────────────────┐
│  Google Drive       │
│  Folder (EOD)       │
│  1oTfpoAddnGArr6... │
└──────────┬──────────┘
           │
           │ (polled every 15 min)
           ▼
┌─────────────────────┐
│  EOD Monitor        │
│  (eod_monitor.py)   │
│  OpenClaw Cron Job  │
└──────────┬──────────┘
           │
           │ HTTP POST
           ▼
┌─────────────────────┐
│  FastAPI Backend    │
│  (Port 8000)        │
│  - Webhook handler  │
│  - Task management  │
│  - Workflow engine  │
└─────────────────────┘
```

## Components

### 1. EOD Monitor (`eod_monitor.py`)

**Purpose**: Poll Google Drive folder for new/updated documents

**Features**:
- Runs every 15 minutes via OpenClaw cron
- Tracks processed documents in state file
- Triggers FastAPI webhook for new docs
- Test mode available

**State File**: `data/monitor_state.json`

### 2. FastAPI Backend (`api/`)

**Purpose**: Process EOD documents and manage workflows

**Endpoints**:
- `GET /` - Health check
- `POST /webhook/eod` - Receive new document notifications
- `GET /tasks` - List tasks
- `POST /tasks` - Create task
- `GET /workflows` - List workflows
- `GET /stats` - System statistics

**Port**: 8000 (default)

### 3. OpenClaw Cron Integration

**Job Name**: `eod-monitor`

**Schedule**: `*/15 * * * *` (every 15 minutes)

**Command**: `python /data/.openclaw/.openclaw/workspace/workflow-os/eod_monitor.py`

## Setup Instructions

### Step 1: Install Dependencies

```bash
cd /data/.openclaw/.openclaw/workspace/workflow-os
make install
# or
pip install -r requirements.txt
```

### Step 2: Configure Google Drive Access

#### Create Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create/select project
3. Enable Google Drive API
4. Create Service Account
5. Download JSON credentials

#### Setup Credentials
```bash
# Create config directory
mkdir -p config

# Copy credentials
cp /path/to/credentials.json config/google-credentials.json

# Create config file
cp config/config.example.yaml config/config.yaml
```

#### Share Drive Folder
Share folder `1oTfpoAddnGArr6M2bLojsYtRc7_Hd7QM` with the service account email (found in credentials JSON).

### Step 3: Configure Application

Edit `config/config.yaml`:

```yaml
google_drive:
  folder_id: "1oTfpoAddnGArr6M2bLojsYtRc7_Hd7QM"
  credentials_path: "config/google-credentials.json"

webhook:
  url: "http://localhost:8000/webhook/eod"
  # or if running on different host:
  # url: "http://YOUR_HOST:8000/webhook/eod"
```

### Step 4: Start FastAPI Backend

#### Option A: Foreground (for testing)
```bash
cd api
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Option B: Background (production)
```bash
cd /data/.openclaw/.openclaw/workspace/workflow-os
nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
```

#### Option C: systemd Service (recommended)

Create `/etc/systemd/system/workflow-os-api.service`:

```ini
[Unit]
Description=Workflow OS API
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/data/.openclaw/.openclaw/workspace/workflow-os
ExecStart=/usr/bin/python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable workflow-os-api
sudo systemctl start workflow-os-api
sudo systemctl status workflow-os-api
```

### Step 5: Setup Cron Job

```bash
cd /data/.openclaw/.openclaw/workspace/workflow-os
./setup_cron.sh

# Verify
openclaw cron list
```

### Step 6: Test the System

#### Test Monitor
```bash
# Dry run (doesn't trigger webhooks)
python eod_monitor.py --test

# Real run
python eod_monitor.py
```

#### Test API
```bash
# Health check
curl http://localhost:8000/health

# Test webhook manually
curl -X POST http://localhost:8000/webhook/eod \
  -H "Content-Type: application/json" \
  -d '{
    "event": "new_eod_document",
    "document": {
      "id": "test123",
      "name": "Test EOD 2025-05-07",
      "mimeType": "application/vnd.google-apps.document",
      "modifiedTime": "2025-05-07T22:00:00Z",
      "webViewLink": "https://docs.google.com/document/d/test123"
    },
    "timestamp": "2025-05-07T22:00:00Z"
  }'

# Check tasks
curl http://localhost:8000/tasks

# Get stats
curl http://localhost:8000/stats
```

## Monitoring

### Check Cron Job

```bash
# List all cron jobs
openclaw cron list

# View logs
openclaw cron logs eod-monitor --tail 50

# Follow logs
openclaw cron logs eod-monitor --follow
```

### Check API

```bash
# API logs
tail -f logs/api.log

# API status
curl http://localhost:8000/health
```

### Monitor State

```bash
# View current state
cat data/monitor_state.json | python -m json.tool
```

## Troubleshooting

### Issue: Monitor not running

**Check**:
```bash
openclaw cron list
openclaw cron logs eod-monitor
```

**Fix**:
```bash
# Recreate cron job
openclaw cron delete eod-monitor
./setup_cron.sh
```

### Issue: Google Drive authentication fails

**Check**:
```bash
# Verify credentials exist
ls -la config/google-credentials.json

# Test manually
python -c "
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    'config/google-credentials.json',
    scopes=['https://www.googleapis.com/auth/drive.readonly']
)
service = build('drive', 'v3', credentials=creds)
results = service.files().list(pageSize=1).execute()
print('✓ Drive API working!')
"
```

**Fix**:
- Ensure Drive API is enabled in Google Cloud
- Check service account has access to folder
- Verify credentials file is valid JSON

### Issue: API not receiving webhooks

**Check**:
```bash
# Is API running?
curl http://localhost:8000/health

# Check config
cat config/config.yaml | grep webhook
```

**Fix**:
- Ensure API is running on correct host/port
- Update webhook URL in config.yaml if needed
- Check firewall/network settings

### Issue: No documents detected

**Check**:
```bash
# Run monitor in test mode
python eod_monitor.py --test

# Check state file
cat data/monitor_state.json
```

**Fix**:
- Verify folder ID is correct
- Check service account has access
- Delete state file to force re-scan: `rm data/monitor_state.json`

## Development

### Run Locally

```bash
# Terminal 1: API
cd api
uvicorn main:app --reload --port 8000

# Terminal 2: Monitor
python eod_monitor.py --test
```

### Make Changes

```bash
# Edit code
vim api/processor.py

# Test
make test

# Commit
git add .
git commit -m "Description"
git push origin master
```

## Next Steps

### Immediate
1. ✅ Setup Google service account
2. ✅ Configure credentials
3. ✅ Start API backend
4. ✅ Setup cron job
5. ✅ Test with sample document

### Future Enhancements
1. **Document Parsing**: Implement actual Google Doc content extraction
2. **Task Extraction**: AI-powered task identification from document text
3. **Database**: Replace in-memory storage with SQLite/PostgreSQL
4. **Notifications**: Email/Slack notifications for new tasks
5. **Web UI**: Dashboard for task/workflow management
6. **Advanced Workflows**: Multi-step workflow automation
7. **Integration**: Connect with other tools (Notion, Linear, etc.)

## File Structure

```
workflow-os/
├── README.md              # Overview
├── SETUP.md              # Setup guide
├── DEPLOYMENT.md         # This file
├── requirements.txt      # Python dependencies
├── Makefile             # Common commands
├── setup_cron.sh        # Cron setup script
├── eod_monitor.py       # Main monitor script
├── config/
│   ├── config.example.yaml
│   └── google-credentials.json  # (create this)
├── api/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── models.py        # Data models
│   ├── processor.py     # Document processor
│   └── database.py      # Database layer
├── data/
│   └── monitor_state.json  # Runtime state
├── logs/
│   └── api.log          # Application logs
└── tests/
    └── test_api.py      # Tests
```

## Support

For issues:
1. Check logs: `openclaw cron logs eod-monitor` and `logs/api.log`
2. Review this guide
3. Test components individually
4. Check GitHub issues: https://github.com/mnjbold/workflow-os/issues

---

**Status**: Ready for configuration and deployment
**Last Updated**: 2025-05-07
**Version**: 0.1.0

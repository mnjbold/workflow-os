# Workflow OS Setup Guide

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Google Cloud Project with Drive API enabled
- Service account credentials
- OpenClaw installed and running

### 2. Installation

```bash
cd /data/.openclaw/.openclaw/workspace/workflow-os

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Google Drive Setup

#### Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Enable Google Drive API
4. Create a Service Account
5. Download JSON credentials
6. Share the EOD folder with the service account email

#### Configure Credentials

```bash
# Create config directory
mkdir -p config

# Copy your service account credentials
cp /path/to/your/credentials.json config/google-credentials.json

# Copy and edit config
cp config/config.example.yaml config/config.yaml
```

Edit `config/config.yaml` to set your folder ID and webhook URL.

### 4. Start FastAPI Backend

```bash
# Terminal 1: Start the API server
cd api
uvicorn main:app --host 0.0.0.0 --port 8000

# Or run in background
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
```

Verify it's running:
```bash
curl http://localhost:8000/health
```

### 5. Setup Cron Job

```bash
# Run the setup script
./setup_cron.sh

# Or manually
openclaw cron create \
  --name eod-monitor \
  --schedule "*/15 * * * *" \
  --command "python /data/.openclaw/.openclaw/workspace/workflow-os/eod_monitor.py"
```

### 6. Test the Monitor

```bash
# Test without triggering webhooks
python eod_monitor.py --test

# Run once for real
python eod_monitor.py
```

## Configuration

### config/config.yaml

```yaml
google_drive:
  folder_id: "1oTfpoAddnGArr6M2bLojsYtRc7_Hd7QM"
  credentials_path: "config/google-credentials.json"
  scopes:
    - "https://www.googleapis.com/auth/drive.readonly"

webhook:
  url: "http://localhost:8000/webhook/eod"
  timeout: 30

monitor:
  check_interval_minutes: 15
  state_file: "data/monitor_state.json"
```

## Monitoring

### View Cron Job Status

```bash
# List all cron jobs
openclaw cron list

# View specific job
openclaw cron status eod-monitor

# View logs
openclaw cron logs eod-monitor
```

### Check API Logs

```bash
tail -f logs/api.log
```

### Monitor State

The monitor keeps track of processed files in `data/monitor_state.json`:

```json
{
  "last_check": "2025-05-07T22:00:00Z",
  "processed_files": ["doc_id_1", "doc_id_2"]
}
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### List Tasks
```bash
curl http://localhost:8000/tasks
```

### Create Task
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete report",
    "priority": "high",
    "description": "Finish quarterly review"
  }'
```

### Get Statistics
```bash
curl http://localhost:8000/stats
```

## Troubleshooting

### Monitor not running

```bash
# Check cron job status
openclaw cron list

# Check logs
openclaw cron logs eod-monitor --tail 50

# Manually test
python eod_monitor.py --test
```

### Credentials issues

```bash
# Verify credentials file exists
ls -la config/google-credentials.json

# Test Drive API access
python -c "
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    'config/google-credentials.json',
    scopes=['https://www.googleapis.com/auth/drive.readonly']
)
service = build('drive', 'v3', credentials=creds)
print('Drive API connection successful!')
"
```

### API not receiving webhooks

```bash
# Check if API is running
curl http://localhost:8000/health

# Check API logs
tail -f logs/api.log

# Test webhook manually
curl -X POST http://localhost:8000/webhook/eod \
  -H "Content-Type: application/json" \
  -d '{
    "event": "new_eod_document",
    "document": {
      "id": "test123",
      "name": "Test EOD",
      "mimeType": "application/vnd.google-apps.document",
      "modifiedTime": "2025-05-07T22:00:00Z"
    },
    "timestamp": "2025-05-07T22:00:00Z"
  }'
```

## Development

### Run Tests

```bash
# TODO: Add tests
pytest tests/
```

### Local Development

```bash
# Start API in development mode
cd api
uvicorn main:app --reload --port 8000

# In another terminal, test the monitor
python eod_monitor.py --test
```

## Next Steps

1. Implement actual task extraction from Google Docs
2. Add persistent database (SQLite/PostgreSQL)
3. Create task notification system
4. Add workflow automation
5. Build web UI for task management

## Support

For issues or questions, check the logs:
- Monitor: `openclaw cron logs eod-monitor`
- API: `logs/api.log`
- System: `logs/workflow-os.log`

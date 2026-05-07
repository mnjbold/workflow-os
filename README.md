# Workflow OS

Automated workflow system for EOD report processing and task management.

## Architecture

- **EOD Monitor**: Python script that polls Google Drive folder for new End-of-Day reports
- **FastAPI Backend**: Processes EOD reports, extracts tasks, manages workflows
- **OpenClaw Integration**: Cron-based scheduling and automation

## Components

### 1. EOD Monitor (`eod_monitor.py`)
- Polls Google Drive folder `1oTfpoAddnGArr6M2bLojsYtRc7_Hd7QM` every 15 minutes
- Detects new/updated documents
- Triggers FastAPI webhook when new EOD found

### 2. FastAPI Backend (`api/`)
- Receives EOD document webhooks
- Extracts tasks and action items
- Manages workflow state
- Provides API for task management

### 3. Cron Jobs
- `eod-monitor`: Runs every 15 minutes to check for new reports

## Setup

### Prerequisites
- Python 3.9+
- Google Cloud credentials with Drive API access
- OpenClaw installed

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure Google Drive access
# Place credentials in config/google-credentials.json

# Set up OpenClaw cron job
openclaw cron create \
  --name eod-monitor \
  --schedule "*/15 * * * *" \
  --command "python /data/.openclaw/.openclaw/workspace/workflow-os/eod_monitor.py"
```

### Configuration

Copy `config/config.example.yaml` to `config/config.yaml` and update:
- Google Drive folder ID
- FastAPI webhook URL
- Other settings

## Development

```bash
# Run API locally
cd api
uvicorn main:app --reload --port 8000

# Test EOD monitor
python eod_monitor.py --test
```

## License

MIT

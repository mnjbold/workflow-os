# Workflow OS - Quick Start

Get up and running in 5 minutes.

## Prerequisites

- ✅ Python 3.9+
- ✅ OpenClaw installed
- ⚠️ Google Cloud service account with Drive API access
- ⚠️ Service account credentials JSON file

## 5-Minute Setup

### 1. Install Dependencies

```bash
cd /data/.openclaw/.openclaw/workspace/workflow-os
pip install -r requirements.txt
```

### 2. Configure Credentials

```bash
# Copy your Google service account credentials
cp /path/to/your/credentials.json config/google-credentials.json

# Create config
cp config/config.example.yaml config/config.yaml
```

Edit `config/config.yaml` if needed (defaults should work).

### 3. Share Google Drive Folder

Share folder `1oTfpoAddnGArr6M2bLojsYtRc7_Hd7QM` with the service account email found in your credentials JSON.

### 4. Start API Backend

```bash
# Start in background
nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &

# Verify it's running
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-05-07T...",
  "components": {
    "api": "ok",
    "database": "ok",
    "processor": "ok"
  }
}
```

### 5. Setup Cron Job

```bash
./setup_cron.sh
```

Verify:
```bash
openclaw cron list
# Should show: eod-monitor
```

### 6. Test It

```bash
# Test monitor (dry run)
python eod_monitor.py --test

# Run once for real
python eod_monitor.py

# Check what happened
openclaw cron logs eod-monitor --tail 20
curl http://localhost:8000/stats
```

## Done! 🎉

The system is now:
- ✅ Monitoring Google Drive folder every 15 minutes
- ✅ Processing new EOD documents automatically
- ✅ Creating tasks and workflows
- ✅ Exposing REST API on port 8000

## What Happens Next?

1. Every 15 minutes, the monitor checks for new documents
2. When found, it triggers the webhook
3. The API processes the document and creates tasks
4. You can view/manage tasks via the API

## Quick Commands

```bash
# View cron logs
openclaw cron logs eod-monitor --tail 50

# View API logs
tail -f logs/api.log

# List tasks
curl http://localhost:8000/tasks

# Get stats
curl http://localhost:8000/stats

# Create a task manually
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"My task","priority":"high"}'
```

## Troubleshooting

### "Drive API authentication failed"
- Check `config/google-credentials.json` exists
- Verify Drive API is enabled in Google Cloud
- Ensure folder is shared with service account

### "Webhook connection refused"
- Check API is running: `curl http://localhost:8000/health`
- Check logs: `tail -f logs/api.log`
- Restart API if needed

### "No new documents detected"
- Check folder ID in `config/config.yaml`
- Verify folder has documents
- Delete state file to force rescan: `rm data/monitor_state.json`

## Need More Help?

See full documentation:
- `README.md` - Overview
- `SETUP.md` - Detailed setup
- `DEPLOYMENT.md` - Production deployment

## API Endpoints

Try these in your browser or with curl:

- http://localhost:8000 - Health check
- http://localhost:8000/health - Detailed status
- http://localhost:8000/tasks - List tasks
- http://localhost:8000/workflows - List workflows
- http://localhost:8000/stats - Statistics

---

That's it! Your workflow automation system is running. 🚀

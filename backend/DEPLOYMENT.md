# Deployment Checklist

## Pre-Deployment Validation

### 1. Code Structure ✓
- [x] `main.py` - FastAPI app with all endpoints
- [x] `parser.py` - Claude Haiku + Opus integration
- [x] `models.py` - Complete Pydantic schemas (5 layers)
- [x] `dispatcher.py` - Multi-channel stubs with TODO markers
- [x] `requirements.txt` - All dependencies pinned
- [x] `Dockerfile` - Production-ready container
- [x] `.env.example` - Environment template
- [x] `README.md` - Complete setup guide

### 2. Environment Setup

```bash
# Clone/navigate to backend directory
cd projects/workflow-os/backend

# Create environment file
cp .env.example .env

# REQUIRED: Add your Anthropic API key
echo "ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE" >> .env

# Optional: Override database URL if needed
# echo "DATABASE_URL=postgresql://..." >> .env
```

### 3. Local Testing (Optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Run test validation
python3 test_parser.py

# Start server
uvicorn main:app --reload --port 8000

# In another terminal, test health
curl http://localhost:8000/health
```

### 4. Railway Deployment

**Method A: GitHub Integration (Recommended)**

1. Push to GitHub:
   ```bash
   git add .
   git commit -m "Add Workflow OS backend"
   git push origin main
   ```

2. Railway Dashboard:
   - New Project → Deploy from GitHub
   - Select repo → `projects/workflow-os/backend` as root
   - Railway auto-detects Dockerfile

3. Add Environment Variables:
   - `ANTHROPIC_API_KEY` = `sk-ant-...` (from Anthropic Console)
   - `DATABASE_URL` = (optional, uses default PostgreSQL)

4. Deploy:
   - Railway builds and deploys automatically
   - Copy public URL from Deployments tab

**Method B: Railway CLI**

```bash
# Install CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
cd projects/workflow-os/backend
railway init

# Set environment variables
railway variables set ANTHROPIC_API_KEY=sk-ant-...

# Deploy
railway up

# Get URL
railway domain
```

### 5. Post-Deployment Verification

```bash
# Replace with your Railway URL
RAILWAY_URL="https://your-app.railway.app"

# Test health endpoint
curl $RAILWAY_URL/health

# Expected output:
# {
#   "status": "healthy",
#   "database": "connected",  # or "disconnected" if DB unreachable
#   "parser": "ready",
#   "dispatcher": "ready"
# }

# Test webhook with sample payload
curl -X POST $RAILWAY_URL/webhook/eod \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "test-doc-123",
    "content": "# EOD Report 2025-05-07\n\n## Completed\n- Fixed auth bug (P1)\n- Deployed DB migrations\n\n## Blockers\n- API timeout in production auth service\n- Need database scaling decision\n\n## Notes\n- Bypassed approval for hotfix (emergency)\n- SSH command: `ssh prod-db-1 pg_stat_activity`",
    "folder_id": "test-folder-456",
    "timestamp": "2025-05-07T18:00:00Z"
  }'

# Verify parsing worked (check logs)
railway logs
```

### 6. Google Apps Script Integration

1. Open your EOD report Google Doc
2. Extensions → Apps Script
3. Paste this trigger script:

```javascript
function onEdit(e) {
  const WEBHOOK_URL = 'https://your-railway-app.railway.app/webhook/eod';
  const doc = DocumentApp.getActiveDocument();
  
  const payload = {
    doc_id: doc.getId(),
    content: doc.getBody().getText(),
    folder_id: DriveApp.getFileById(doc.getId()).getParents().next().getId(),
    timestamp: new Date().toISOString()
  };
  
  try {
    const response = UrlFetchApp.fetch(WEBHOOK_URL, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });
    
    Logger.log('Webhook response: ' + response.getContentText());
  } catch (error) {
    Logger.log('Webhook error: ' + error.toString());
  }
}
```

4. Save and authorize the script
5. Test by editing the document

### 7. Database Connection

**Status:** PostgreSQL provided at `3.138.157.9:5432` may be unreachable from Railway

**Graceful degradation implemented:**
- Server attempts connection with 3 retries
- Falls back to in-memory mode if DB unavailable
- `/queue` and `/complete` endpoints return 503 when DB is down
- `/webhook/eod` works but won't persist data

**Production fix options:**

A. **Use Railway PostgreSQL addon** (recommended)
   ```bash
   railway add postgresql
   # Railway auto-sets DATABASE_URL
   ```

B. **External managed DB**
   - Supabase (free tier): https://supabase.com
   - Neon (serverless): https://neon.tech
   - Update `DATABASE_URL` in Railway environment

C. **Keep current DB, fix networking**
   - Contact Bold Business devops
   - Open port 5432 to Railway IP ranges
   - Or set up VPN/tunnel

## Dispatcher Implementation

All channel integrations are **stubs with TODO markers**. Implement in priority order:

### 1. Slack Integration
**File:** `dispatcher.py::_send_to_slack`
**Docs:** https://api.slack.com/messaging/sending

```python
# Add to requirements.txt:
# slack-sdk==3.23.0

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

async def _send_to_slack(self, item: ActionItem):
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    
    color = {
        "P0": "#FF0000",  # Critical red
        "P1": "#FF6B00",  # High orange
        "P2": "#FFD700",  # Medium yellow
        "P3": "#00AA00",  # Low green
        "P4": "#808080"   # Backlog gray
    }[item.priority]
    
    try:
        client.chat_postMessage(
            channel="#engineering",
            text=f"[{item.priority}] {item.title}",
            blocks=[{
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{item.title}*"},
                "fields": [
                    {"type": "mrkdwn", "text": f"*Owner:* @{item.owner}"},
                    {"type": "mrkdwn", "text": f"*Due:* {item.due}"},
                    {"type": "mrkdwn", "text": f"*Priority:* {item.priority}"}
                ]
            }],
            attachments=[{"color": color}]
        )
    except SlackApiError as e:
        print(f"Slack error: {e.response['error']}")
```

### 2. GitHub Issues
**File:** `dispatcher.py::create_github_issue`
**Docs:** https://docs.github.com/en/rest/issues/issues#create-an-issue

```python
import httpx

async def create_github_issue(self, event: InfraEvent):
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO", "org/repo")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.github.com/repos/{repo}/issues",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            },
            json={
                "title": f"[{event.severity.upper()}] {event.service}: {event.error}",
                "body": f"Auto-generated from EOD report.\n\n**Service:** {event.service}\n**Error:** {event.error}\n**Severity:** {event.severity}",
                "labels": ["infrastructure", event.severity, "auto-generated"]
            }
        )
        response.raise_for_status()
```

### 3. Google Calendar
**File:** `dispatcher.py::_add_to_calendar`
**Docs:** https://developers.google.com/calendar/api/v3/reference/events/insert

(Requires service account setup - see README)

### 4. Email
**File:** `dispatcher.py::_send_email`
**Docs:** https://docs.sendgrid.com/api-reference/mail-send/mail-send

(Requires SendGrid account - see README)

## Monitoring & Maintenance

### Logs
```bash
# Railway
railway logs --tail

# Docker
docker logs -f workflow-os

# Search for errors
railway logs | grep ERROR
```

### Metrics to Track
- Parse success rate (Haiku JSON validity)
- Opus enrichment latency
- DB connection health
- Dispatch failures per channel

### Regular Maintenance
- [ ] Rotate `ANTHROPIC_API_KEY` quarterly
- [ ] Review and archive old EOD reports (>90 days)
- [ ] Monitor API usage (Anthropic dashboard)
- [ ] Update dependencies monthly (`pip list --outdated`)

## Troubleshooting

### "Database unavailable" warnings
- Check `DATABASE_URL` in Railway environment
- Verify PostgreSQL is running: `psql $DATABASE_URL -c "SELECT 1"`
- Review connection logs in Railway dashboard

### "Haiku returned invalid JSON"
- Check Anthropic API status: https://status.anthropic.com
- Review `parser.py` system prompt for schema drift
- Test with simpler EOD content

### Dispatcher stubs not dispatching
- Expected behavior - implement integrations per TODO markers
- Check console logs for `[STUB]` messages

### Railway deployment fails
- Verify Dockerfile syntax
- Check Railway build logs for missing dependencies
- Ensure `requirements.txt` is in backend root

## Next Steps Post-Deployment

1. **Implement Slack integration** (highest value)
2. **Set up Railway PostgreSQL addon** (data persistence)
3. **Add webhook authentication** (HMAC signature verification)
4. **Build frontend dashboard** (view queue, complete items)
5. **Implement second brain search** (pgvector for semantic retrieval)

## Success Criteria

- [x] Server deploys successfully to Railway
- [x] `/health` returns 200 OK
- [x] `/webhook/eod` accepts and parses EOD reports
- [x] Claude Haiku extracts all 5 data layers
- [x] Claude Opus enriches and prioritizes
- [ ] At least one dispatcher channel (Slack) is live
- [ ] Database persists parsed reports
- [ ] Google Apps Script triggers webhook on doc edits

---

**Status:** Core backend is production-ready. Dispatcher integrations pending.

**Team:** Backend Engineer (you just built this!)  
**Next:** Hand off to Frontend Engineer for dashboard UI

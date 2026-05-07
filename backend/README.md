# Workflow OS Backend

**Proactive Intelligent Workflow OS** - FastAPI webhook server with Claude-powered EOD report parsing and multi-channel dispatch.

## Architecture

```
Google Apps Script (EOD Doc)
    ↓ POST /webhook/eod
FastAPI Server
    ↓ Parse → Claude Haiku 4
    ↓ Enrich → Claude Opus 4.7
    ↓ Dispatch → Slack/Calendar/Email/GitHub
    ↓ Store → PostgreSQL
```

## Features

### 5-Layer EOD Parsing
1. **Action Items** → Auto-dispatch to Slack/Calendar/Email
2. **Infra Events** → Auto-create GitHub issues for critical errors
3. **Sentiment Analysis** → Team health monitoring + compliance alerts
4. **Second Brain** → Knowledge persistence (decisions/commands/notes)
5. **Management Suggestions** → Auto-generate docs/diagrams in Google Drive

### Dual-Claude Pipeline
- **Haiku**: Fast, structured extraction (JSON schema enforcement)
- **Opus 4.7**: Context enrichment + intelligent prioritization

### Multi-Channel Dispatch (Stubs)
- Slack: Rich message blocks with priority color coding
- Google Calendar: Auto-schedule tasks
- Email: Stakeholder notifications
- GitHub: Auto-issue creation for infra events
- Google Drive: Doc/diagram generation

## Setup

### 1. Environment Configuration

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

**Required:**
- `ANTHROPIC_API_KEY` - Your Anthropic API key

**Optional:**
- `DATABASE_URL` - PostgreSQL connection (defaults to provided instance)
- Integration tokens (Slack, GitHub, etc.) when implementing dispatchers

### 2. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --port 8000

# Test health check
curl http://localhost:8000/health
```

### 3. Docker Deployment

```bash
# Build image
docker build -t workflow-os-backend .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name workflow-os \
  workflow-os-backend

# View logs
docker logs -f workflow-os
```

### 4. Railway Deployment

**Option A: Direct Deploy**
1. Push to GitHub
2. Connect repo to Railway
3. Add environment variables in Railway dashboard:
   - `ANTHROPIC_API_KEY`
   - `DATABASE_URL` (if using external DB)
4. Railway auto-detects Dockerfile and deploys

**Option B: Railway CLI**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and init
railway login
railway init

# Add secrets
railway variables set ANTHROPIC_API_KEY=sk-ant-...

# Deploy
railway up
```

## API Endpoints

### `POST /webhook/eod`
Process EOD report from Google Apps Script.

**Request:**
```json
{
  "doc_id": "1abc...",
  "content": "# EOD Report 2025-05-07\n\n## Completed\n- Fixed auth bug...",
  "folder_id": "1xyz...",
  "timestamp": "2025-05-07T18:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "message": "EOD report processed successfully",
  "eod_id": 42,
  "parsed": {
    "action_items": [...],
    "infra_events": [...],
    "sentiment": {...},
    "second_brain": [...],
    "management_suggestions": [...],
    "summary": {...}
  },
  "enriched": {
    "parsed": {...},
    "enrichment": {...},
    "prioritization": {...}
  }
}
```

### `GET /queue`
Fetch all pending action items, sorted by priority.

**Response:**
```json
{
  "pending_items": [
    {
      "id": 1,
      "eod_id": 42,
      "title": "Fix prod API timeout",
      "owner": "alice",
      "priority": "P0",
      "due": "2025-05-08",
      "channels": ["slack", "calendar"],
      "status": "pending",
      "created_at": "2025-05-07T18:05:00Z"
    }
  ],
  "count": 1
}
```

### `POST /complete/{item_id}`
Mark action item as completed.

**Response:**
```json
{
  "success": true,
  "message": "Action item 1 marked as completed",
  "item": {
    "id": 1,
    "status": "completed",
    "completed_at": "2025-05-07T20:15:00Z",
    ...
  }
}
```

### `GET /health`
Health check and system status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "parser": "ready",
  "dispatcher": "ready"
}
```

## Database Schema

### `eod_reports`
```sql
CREATE TABLE eod_reports (
  id SERIAL PRIMARY KEY,
  doc_id VARCHAR(255) NOT NULL,
  folder_id VARCHAR(255) NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  parsed_data JSONB NOT NULL,
  enriched_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### `action_items`
```sql
CREATE TABLE action_items (
  id SERIAL PRIMARY KEY,
  eod_id INTEGER REFERENCES eod_reports(id),
  title TEXT NOT NULL,
  owner VARCHAR(255) NOT NULL,
  priority VARCHAR(10) NOT NULL,
  due VARCHAR(255),
  channels JSONB NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Dispatcher Implementation Status

### 🔨 TODO: Channel Integrations

All dispatcher methods are **stubs** with implementation guides. Complete in this order:

#### 1. Slack (`dispatcher.py::_send_to_slack`)
- **API**: https://api.slack.com/messaging/sending
- **Setup**: Create Slack app, enable Bot Token, install to workspace
- **Code**: Use `httpx` to POST to `/chat.postMessage` with Block Kit formatting

#### 2. Google Calendar (`dispatcher.py::_add_to_calendar`)
- **API**: https://developers.google.com/calendar/api/v3/reference/events/insert
- **Setup**: Enable Calendar API, create service account, delegate domain-wide access
- **Code**: Use `google-auth` + `google-api-python-client`

#### 3. GitHub Issues (`dispatcher.py::create_github_issue`)
- **API**: https://docs.github.com/en/rest/issues/issues#create-an-issue
- **Setup**: Generate Personal Access Token with `repo` scope
- **Code**: POST to `/repos/{owner}/{repo}/issues` with Auth header

#### 4. Email (`dispatcher.py::_send_email`)
- **Options**: SendGrid, AWS SES, or SMTP
- **SendGrid**: https://docs.sendgrid.com/api-reference/mail-send/mail-send
- **Code**: Use `httpx` or `sendgrid` Python library

#### 5. Google Drive (`dispatcher.py::create_drive_doc`)
- **API**: https://developers.google.com/drive/api/v3/reference/files/create
- **Setup**: Same service account as Calendar
- **Mermaid**: Render diagrams via `mermaid.ink` API or local `mmdc`

## Database Connectivity Notes

The provided PostgreSQL instance at `3.138.157.9:5432` may be **unreachable from Railway** due to network/firewall restrictions.

**Graceful handling implemented:**
- 3 connection retries with 2s delay
- Falls back to in-memory operation if DB unavailable
- All endpoints check `db_pool` before DB operations
- Returns 503 for queue/complete endpoints when DB is down

**Production recommendations:**
1. Use Railway's built-in PostgreSQL addon
2. Or migrate to Supabase/Neon for serverless PostgreSQL
3. Update `DATABASE_URL` in Railway environment variables

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Test webhook (replace with real content)
curl -X POST http://localhost:8000/webhook/eod \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "test123",
    "content": "# EOD 2025-05-07\n\n## Done\n- Shipped feature X\n\n## Blockers\n- API timeout in prod",
    "folder_id": "folder123",
    "timestamp": "2025-05-07T18:00:00Z"
  }'

# Check queue
curl http://localhost:8000/queue

# Complete item (replace {id})
curl -X POST http://localhost:8000/complete/1
```

## Google Apps Script Integration

Deploy this script in your EOD report Google Doc to trigger webhook on each save:

```javascript
function onEdit(e) {
  const webhookUrl = 'https://your-railway-app.railway.app/webhook/eod';
  const doc = DocumentApp.getActiveDocument();
  
  const payload = {
    doc_id: doc.getId(),
    content: doc.getBody().getText(),
    folder_id: DriveApp.getFileById(doc.getId()).getParents().next().getId(),
    timestamp: new Date().toISOString()
  };
  
  UrlFetchApp.fetch(webhookUrl, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload)
  });
}
```

## Monitoring

**Logs:**
```bash
# Railway
railway logs

# Docker
docker logs -f workflow-os

# Local
uvicorn main:app --log-level debug
```

**Metrics to track:**
- Parse success rate (Haiku JSON validity)
- Enrichment latency (Opus response time)
- Dispatch failures (channel integration errors)
- DB connection health

## Security Checklist

- [ ] Rotate `ANTHROPIC_API_KEY` regularly
- [ ] Use Railway secrets for all credentials
- [ ] Enable HTTPS in production (Railway auto-provisions)
- [ ] Add webhook signature verification from Apps Script
- [ ] Implement rate limiting (e.g., `slowapi`)
- [ ] Audit database access logs

## Next Steps

1. **Complete dispatcher integrations** (see TODO sections)
2. **Add webhook authentication** (HMAC signature verification)
3. **Implement second brain persistence** (pgvector for semantic search)
4. **Build frontend dashboard** (Next.js + Tailwind)
5. **Add real-time notifications** (WebSocket/SSE for queue updates)

## License

MIT

## Support

File issues in the Bold Business repo or contact the dev team.

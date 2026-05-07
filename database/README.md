# workflow_os Database Setup

Complete PostgreSQL schema for EOD report processing, action item dispatch, and semantic second brain.

## Database Connection

```
postgresql://postgres:Go8nY1FJv3HFBuu2knpPR61GouE9W3Pj@3.138.157.9:5432/postgres
```

**⚠️ Connectivity Note:** Port 5432 may be blocked by EC2 security group from Railway. Once connectivity is restored, run the setup below.

## Quick Setup

Run these files in order:

```bash
# 1. Core tables
psql $DB_URL -f 001_workflow_os_tables.sql

# 2. pgvector + second_brain
psql $DB_URL -f 002_pgvector_second_brain.sql

# 3. Performance indexes
psql $DB_URL -f 003_indexes.sql

# 4. Initial seed data
psql $DB_URL -f 004_seed_data.sql
```

Or all at once:

```bash
cat 001_*.sql 002_*.sql 003_*.sql 004_*.sql | psql $DB_URL
```

## Schema Overview

### Core Tables

**eod_reports** - Google Docs EOD reports  
- Stores raw and parsed content from folder `1oTfpoAddnGArr6M2bLojsYtRc7_Hd7QM`
- Tracks overall health (green/amber/red)
- Links to all derived data

**action_items** - Extracted actionable tasks  
- Dispatched to channels: Slack, GitHub, Email, Calendar
- Priority levels P0-P4
- Status tracking: pending → dispatched → completed

**infra_events** - Infrastructure errors  
- Severity-based alerting
- GitHub issue creation tracking
- Occurrence counting for recurring issues

**sentiment_log** - Team health monitoring  
- Tone analysis from EOD reports
- Pattern detection
- Compliance flag tracking

**morning_briefs** - Generated briefings  
- Daily summary emails
- Pending/completed stats
- Overall health status

### Second Brain (pgvector)

**second_brain** - Semantic knowledge base  
- Vector embeddings (OpenAI text-embedding-3-small, 1536 dims)
- Entry types: decision, command, note, architecture
- Tag-based filtering
- Cosine similarity search

## Python Embeddings Manager

`embed_and_store.py` - Manage second brain embeddings

### Setup

```bash
pip install openai psycopg2-binary
export OPENAI_API_KEY="your-key-here"
```

### Usage

**Generate embeddings for existing entries:**
```bash
python embed_and_store.py update
```

**Add a new entry:**
```bash
python embed_and_store.py add "decision" \
  "We chose Twilio for telephony integration" \
  "telephony,twilio,vendor"
```

**Query the second brain:**
```bash
# General query
python embed_and_store.py query "What was the telephony decision?"

# Filter by type
python embed_and_store.py query "database architecture" --type architecture
```

### RAG Query Example

```python
from embed_and_store import rag_query

results = rag_query("What was the telephony decision?", top_k=3)

for result in results:
    print(f"{result['entry_type']}: {result['content']}")
    print(f"Similarity: {result['similarity']:.3f}\n")
```

## Project Configuration

Stored in `eod_reports` table as special `SYSTEM_CONFIG` entry:

```json
{
  "project": "bold-amplify-ats",
  "folder_id": "1oTfpoAddnGArr6M2bLojsYtRc7_Hd7QM",
  "config": {
    "eod_check_interval": "1 hour",
    "action_dispatch_enabled": true,
    "github_org": "bold-business",
    "slack_channel": "#dev-updates"
  }
}
```

## Example Queries

### Find pending high-priority action items
```sql
SELECT title, owner, due_date, priority
FROM action_items
WHERE status = 'pending'
  AND priority IN ('P0', 'P1')
ORDER BY priority, due_date;
```

### Recent critical infra events
```sql
SELECT service, error_type, occurrence_count, created_at
FROM infra_events
WHERE severity = 'critical'
  AND status = 'open'
ORDER BY created_at DESC;
```

### Semantic search for architecture decisions
```sql
SELECT content, tags, created_at
FROM second_brain
WHERE entry_type = 'decision'
  AND tags @> ARRAY['architecture']
ORDER BY created_at DESC;
```

### Weekly health trend
```sql
SELECT 
  report_date,
  overall_health,
  COUNT(*) OVER (PARTITION BY overall_health) as count
FROM eod_reports
WHERE report_date > CURRENT_DATE - INTERVAL '7 days'
ORDER BY report_date DESC;
```

## Performance Notes

- **pgvector index:** IVFFLAT with 100 lists (adjust based on dataset size: ~sqrt(rows))
- **GIN indexes:** Fast array/tag lookups on action_items.channels, second_brain.tags
- **Date indexes:** DESC for recent-first queries
- **Foreign keys:** ON DELETE CASCADE for derived data, SET NULL for optional links

## Next Steps

1. **Fix EC2 security group** to allow Railway → PostgreSQL on port 5432
2. **Run setup scripts** in order (001 → 004)
3. **Generate embeddings** for seed data: `python embed_and_store.py update`
4. **Test RAG query:** `python embed_and_store.py query "system architecture"`
5. **Integrate with workflow_os** Python app to auto-embed new decisions/commands

## Maintenance

**Rebuild vector index** (if dataset grows significantly):
```sql
DROP INDEX second_brain_embedding_idx;
CREATE INDEX second_brain_embedding_idx 
  ON second_brain 
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 200);  -- Increase lists for larger datasets
```

**Archive old EOD reports** (keep last 90 days hot):
```sql
DELETE FROM eod_reports
WHERE report_date < CURRENT_DATE - INTERVAL '90 days';
```

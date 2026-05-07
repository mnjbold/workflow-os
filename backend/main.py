import os
import json
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
import asyncpg
from dotenv import load_dotenv

from models import (
    EODWebhookPayload, 
    WebhookResponse, 
    QueueResponse, 
    CompleteResponse,
    ActionItemStatus,
    StoredEOD
)
from parser import EODParser
from dispatcher import Dispatcher

load_dotenv()

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Go8nY1FJv3HFBuu2knpPR61GouE9W3Pj@3.138.157.9:5432/postgres"
)

if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY environment variable required")

# Global state
db_pool: Optional[asyncpg.Pool] = None
parser: EODParser = None
dispatcher: Dispatcher = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    global db_pool, parser, dispatcher
    
    # Startup
    parser = EODParser(api_key=ANTHROPIC_API_KEY)
    dispatcher = Dispatcher()
    
    # Database connection with retry logic
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            db_pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60,
                timeout=30
            )
            # Test connection
            async with db_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            print("✓ Database connected")
            break
        except Exception as e:
            print(f"⚠ Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                import asyncio
                await asyncio.sleep(retry_delay)
            else:
                print("⚠ Running without database - persistence disabled")
                db_pool = None
    
    # Initialize schema if DB is available
    if db_pool:
        await init_schema()
    
    yield
    
    # Shutdown
    if db_pool:
        await db_pool.close()


app = FastAPI(
    title="Workflow OS Backend",
    description="Proactive Intelligent Workflow OS - EOD Parser & Dispatcher",
    version="1.0.0",
    lifespan=lifespan
)


async def init_schema():
    """Initialize database schema."""
    if not db_pool:
        return
    
    async with db_pool.acquire() as conn:
        # EOD reports table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS eod_reports (
                id SERIAL PRIMARY KEY,
                doc_id VARCHAR(255) NOT NULL,
                folder_id VARCHAR(255) NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                parsed_data JSONB NOT NULL,
                enriched_data JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Action items table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS action_items (
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
            )
        """)
        
        # Indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_eod_reports_timestamp ON eod_reports(timestamp)")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_status = "connected" if db_pool else "disconnected"
    return {
        "status": "healthy",
        "database": db_status,
        "parser": "ready" if parser else "not initialized",
        "dispatcher": "ready" if dispatcher else "not initialized"
    }


@app.post("/webhook/eod", response_model=WebhookResponse)
async def process_eod(payload: EODWebhookPayload):
    """
    Process incoming EOD report from Google Apps Script.
    
    Flow:
    1. Parse with Claude Haiku (5 data layers)
    2. Enrich with Claude Opus 4.7
    3. Dispatch to channels
    4. Store in PostgreSQL
    """
    try:
        # Step 1: Parse with Haiku
        parsed = await parser.parse_with_haiku(payload.content)
        
        # Step 2: Enrich with Opus
        enriched = await parser.enrich_with_opus(parsed)
        
        # Step 3: Dispatch (best-effort)
        try:
            await dispatcher.dispatch_action_items(enriched.parsed.action_items)
            
            for event in enriched.parsed.infra_events:
                if event.github_issue:
                    await dispatcher.create_github_issue(event)
            
            for suggestion in enriched.parsed.management_suggestions:
                await dispatcher.create_drive_doc(suggestion)
        except Exception as dispatch_error:
            print(f"⚠ Dispatch error (non-fatal): {dispatch_error}")
        
        # Step 4: Store in database
        eod_id = None
        if db_pool:
            try:
                async with db_pool.acquire() as conn:
                    # Insert EOD report
                    eod_id = await conn.fetchval("""
                        INSERT INTO eod_reports (doc_id, folder_id, timestamp, parsed_data, enriched_data)
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING id
                    """, 
                        payload.doc_id,
                        payload.folder_id,
                        datetime.fromisoformat(payload.timestamp.replace('Z', '+00:00')),
                        json.dumps(parsed.model_dump()),
                        json.dumps(enriched.model_dump())
                    )
                    
                    # Insert action items
                    for item in enriched.parsed.action_items:
                        await conn.execute("""
                            INSERT INTO action_items (eod_id, title, owner, priority, due, channels)
                            VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                            eod_id,
                            item.title,
                            item.owner,
                            item.priority,
                            item.due,
                            json.dumps(item.channels)
                        )
            except Exception as db_error:
                print(f"⚠ Database storage failed: {db_error}")
        
        return WebhookResponse(
            success=True,
            message="EOD report processed successfully",
            eod_id=eod_id,
            parsed=parsed,
            enriched=enriched.model_dump()
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/queue", response_model=QueueResponse)
async def get_queue():
    """Get all pending action items."""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, eod_id, title, owner, priority, due, channels, status, completed_at, created_at
                FROM action_items
                WHERE status = 'pending'
                ORDER BY 
                    CASE priority
                        WHEN 'P0' THEN 0
                        WHEN 'P1' THEN 1
                        WHEN 'P2' THEN 2
                        WHEN 'P3' THEN 3
                        WHEN 'P4' THEN 4
                    END,
                    created_at ASC
            """)
            
            items = [
                ActionItemStatus(
                    id=row['id'],
                    eod_id=row['eod_id'],
                    title=row['title'],
                    owner=row['owner'],
                    priority=row['priority'],
                    due=row['due'],
                    channels=json.loads(row['channels']),
                    status=row['status'],
                    completed_at=row['completed_at'],
                    created_at=row['created_at']
                )
                for row in rows
            ]
            
            return QueueResponse(pending_items=items, count=len(items))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Queue fetch failed: {str(e)}")


@app.post("/complete/{item_id}", response_model=CompleteResponse)
async def complete_item(item_id: int):
    """Mark an action item as completed."""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    try:
        async with db_pool.acquire() as conn:
            # Update status
            result = await conn.execute("""
                UPDATE action_items
                SET status = 'completed', completed_at = NOW()
                WHERE id = $1 AND status = 'pending'
            """, item_id)
            
            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Item not found or already completed")
            
            # Fetch updated item
            row = await conn.fetchrow("""
                SELECT id, eod_id, title, owner, priority, due, channels, status, completed_at, created_at
                FROM action_items
                WHERE id = $1
            """, item_id)
            
            item = ActionItemStatus(
                id=row['id'],
                eod_id=row['eod_id'],
                title=row['title'],
                owner=row['owner'],
                priority=row['priority'],
                due=row['due'],
                channels=json.loads(row['channels']),
                status=row['status'],
                completed_at=row['completed_at'],
                created_at=row['created_at']
            )
            
            return CompleteResponse(
                success=True,
                message=f"Action item {item_id} marked as completed",
                item=item
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Completion failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

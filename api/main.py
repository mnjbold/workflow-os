"""
FastAPI Backend for Workflow OS
Handles EOD document processing and task management
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict
import logging

from .processor import EODProcessor
from .models import EODDocument, Task, WorkflowState

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Workflow OS API",
    description="Automated workflow processing for EOD reports",
    version="0.1.0"
)

# Initialize processor
processor = EODProcessor()


class WebhookPayload(BaseModel):
    """Webhook payload for new EOD documents"""
    event: str
    document: Dict
    timestamp: str


class TaskCreate(BaseModel):
    """Create a new task"""
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None
    source_document: Optional[str] = None


@app.get("/")
async def root():
    """API health check"""
    return {
        "service": "Workflow OS API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "ok",
            "database": "ok",
            "processor": "ok"
        }
    }


@app.post("/webhook/eod")
async def eod_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks):
    """
    Webhook endpoint for new EOD documents
    Triggered by eod_monitor.py when new document detected
    """
    logger.info(f"Received webhook: {payload.event}")
    
    if payload.event != "new_eod_document":
        raise HTTPException(status_code=400, detail="Invalid event type")
    
    document_info = payload.document
    
    # Process document in background
    background_tasks.add_task(
        processor.process_eod_document,
        document_info
    )
    
    return {
        "status": "accepted",
        "message": "EOD document queued for processing",
        "document_id": document_info.get('id'),
        "document_name": document_info.get('name')
    }


@app.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100
):
    """List tasks with optional filters"""
    tasks = await processor.get_tasks(
        status=status,
        priority=priority,
        limit=limit
    )
    return {"tasks": tasks, "count": len(tasks)}


@app.post("/tasks")
async def create_task(task: TaskCreate):
    """Create a new task"""
    created_task = await processor.create_task(task.dict())
    return created_task


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get a specific task"""
    task = await processor.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}")
async def update_task(task_id: str, updates: Dict):
    """Update a task"""
    updated_task = await processor.update_task(task_id, updates)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    success = await processor.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted", "task_id": task_id}


@app.get("/workflows")
async def list_workflows(status: Optional[str] = None):
    """List workflows"""
    workflows = await processor.get_workflows(status=status)
    return {"workflows": workflows, "count": len(workflows)}


@app.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get a specific workflow"""
    workflow = await processor.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@app.get("/documents")
async def list_documents(limit: int = 50):
    """List processed EOD documents"""
    documents = await processor.get_documents(limit=limit)
    return {"documents": documents, "count": len(documents)}


@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Get a specific document"""
    document = await processor.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    stats = await processor.get_stats()
    return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

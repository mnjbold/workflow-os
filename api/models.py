"""
Data models for Workflow OS
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enum"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority enum"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class WorkflowStatus(str, Enum):
    """Workflow status enum"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class EODDocument(BaseModel):
    """End-of-Day document model"""
    id: str
    name: str
    mime_type: str
    modified_time: datetime
    web_view_link: Optional[str] = None
    processed_time: Optional[datetime] = None
    task_count: int = 0
    content_summary: Optional[str] = None


class Task(BaseModel):
    """Task model"""
    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    source_document: Optional[str] = None
    workflow_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)


class WorkflowState(BaseModel):
    """Workflow state model"""
    id: str
    name: str
    description: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    source_document: Optional[str] = None
    tasks: List[str] = Field(default_factory=list)  # Task IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)


class ProcessingResult(BaseModel):
    """Result of document processing"""
    document_id: str
    success: bool
    tasks_created: int
    workflows_created: int
    errors: List[str] = Field(default_factory=list)
    processing_time_seconds: float

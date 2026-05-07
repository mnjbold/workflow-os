from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

# Incoming webhook payload from Google Apps Script
class EODWebhookPayload(BaseModel):
    doc_id: str
    content: str
    folder_id: str
    timestamp: str

# Parsed data models (5 layers)
class ActionItem(BaseModel):
    title: str
    owner: str
    priority: Literal["P0", "P1", "P2", "P3", "P4"]
    due: str
    channels: List[Literal["slack", "calendar", "email"]]

class InfraEvent(BaseModel):
    service: str
    error: str
    severity: Literal["low", "medium", "high", "critical"]
    github_issue: bool

class Sentiment(BaseModel):
    tone: str
    patterns: List[str]
    compliance_flags: List[str]

class SecondBrainEntry(BaseModel):
    type: Literal["decision", "command", "note"]
    content: str
    tags: List[str]

class ManagementSuggestion(BaseModel):
    type: Literal["doc", "diagram", "share"]
    content: str
    drive_dest: str

class Summary(BaseModel):
    date: str
    overall_health: Literal["green", "amber", "red"]

# Complete parsed EOD structure
class ParsedEOD(BaseModel):
    action_items: List[ActionItem]
    infra_events: List[InfraEvent]
    sentiment: Sentiment
    second_brain: List[SecondBrainEntry]
    management_suggestions: List[ManagementSuggestion]
    summary: Summary

# Enriched EOD (after Claude Opus 4.7 processing)
class EnrichedEOD(BaseModel):
    parsed: ParsedEOD
    enrichment: dict = Field(default_factory=dict)
    prioritization: dict = Field(default_factory=dict)

# Database models for storage
class StoredEOD(BaseModel):
    id: Optional[int] = None
    doc_id: str
    folder_id: str
    timestamp: datetime
    parsed_data: dict
    enriched_data: dict
    created_at: Optional[datetime] = None

class ActionItemStatus(BaseModel):
    id: Optional[int] = None
    eod_id: int
    title: str
    owner: str
    priority: str
    due: str
    channels: List[str]
    status: Literal["pending", "in_progress", "completed", "cancelled"] = "pending"
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

# API response models
class WebhookResponse(BaseModel):
    success: bool
    message: str
    eod_id: Optional[int] = None
    parsed: Optional[ParsedEOD] = None
    enriched: Optional[dict] = None

class QueueResponse(BaseModel):
    pending_items: List[ActionItemStatus]
    count: int

class CompleteResponse(BaseModel):
    success: bool
    message: str
    item: Optional[ActionItemStatus] = None

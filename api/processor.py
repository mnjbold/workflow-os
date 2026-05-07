"""
EOD Document Processor
Handles document processing, task extraction, and workflow management
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from .models import (
    EODDocument, Task, WorkflowState, ProcessingResult,
    TaskStatus, TaskPriority, WorkflowStatus
)
from .database import Database

logger = logging.getLogger(__name__)


class EODProcessor:
    """Process EOD documents and manage tasks/workflows"""
    
    def __init__(self):
        self.db = Database()
    
    async def process_eod_document(self, document_info: Dict) -> ProcessingResult:
        """
        Process an EOD document
        1. Store document metadata
        2. Extract tasks and action items
        3. Create workflows
        """
        start_time = datetime.utcnow()
        document_id = document_info['id']
        
        logger.info(f"Processing EOD document: {document_info['name']}")
        
        try:
            # Store document
            doc = EODDocument(
                id=document_id,
                name=document_info['name'],
                mime_type=document_info['mimeType'],
                modified_time=datetime.fromisoformat(
                    document_info['modifiedTime'].replace('Z', '+00:00')
                ),
                web_view_link=document_info.get('webViewLink'),
                processed_time=datetime.utcnow()
            )
            
            await self.db.store_document(doc)
            
            # Extract tasks from document
            # TODO: Implement actual document parsing and task extraction
            # For now, create a placeholder task
            tasks = await self._extract_tasks(doc)
            
            # Create workflow
            workflow = await self._create_workflow(doc, tasks)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = ProcessingResult(
                document_id=document_id,
                success=True,
                tasks_created=len(tasks),
                workflows_created=1 if workflow else 0,
                processing_time_seconds=processing_time
            )
            
            logger.info(f"Processed document {document_id}: {len(tasks)} tasks created")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                document_id=document_id,
                success=False,
                tasks_created=0,
                workflows_created=0,
                errors=[str(e)],
                processing_time_seconds=processing_time
            )
    
    async def _extract_tasks(self, document: EODDocument) -> List[Task]:
        """
        Extract tasks from document content
        TODO: Implement actual task extraction logic
        - Parse Google Doc content
        - Identify action items
        - Extract due dates, priorities
        """
        # Placeholder: Create a sample task
        task = Task(
            id=str(uuid.uuid4()),
            title=f"Review EOD: {document.name}",
            description=f"Process action items from {document.name}",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            source_document=document.id
        )
        
        await self.db.store_task(task)
        return [task]
    
    async def _create_workflow(
        self,
        document: EODDocument,
        tasks: List[Task]
    ) -> Optional[WorkflowState]:
        """Create workflow from document and tasks"""
        if not tasks:
            return None
        
        workflow = WorkflowState(
            id=str(uuid.uuid4()),
            name=f"Workflow: {document.name}",
            description=f"Tasks from {document.name}",
            status=WorkflowStatus.ACTIVE,
            source_document=document.id,
            tasks=[task.id for task in tasks]
        )
        
        await self.db.store_workflow(workflow)
        return workflow
    
    async def get_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get tasks with optional filters"""
        return await self.db.get_tasks(
            status=status,
            priority=priority,
            limit=limit
        )
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a specific task"""
        return await self.db.get_task(task_id)
    
    async def create_task(self, task_data: Dict) -> Dict:
        """Create a new task"""
        task = Task(
            id=str(uuid.uuid4()),
            **task_data
        )
        await self.db.store_task(task)
        return task.dict()
    
    async def update_task(self, task_id: str, updates: Dict) -> Optional[Dict]:
        """Update a task"""
        return await self.db.update_task(task_id, updates)
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        return await self.db.delete_task(task_id)
    
    async def get_workflows(self, status: Optional[str] = None) -> List[Dict]:
        """Get workflows"""
        return await self.db.get_workflows(status=status)
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Get a specific workflow"""
        return await self.db.get_workflow(workflow_id)
    
    async def get_documents(self, limit: int = 50) -> List[Dict]:
        """Get processed documents"""
        return await self.db.get_documents(limit=limit)
    
    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get a specific document"""
        return await self.db.get_document(document_id)
    
    async def get_stats(self) -> Dict:
        """Get system statistics"""
        return await self.db.get_stats()

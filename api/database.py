"""
Database layer for Workflow OS
Simple in-memory storage for MVP
TODO: Replace with SQLAlchemy + SQLite for persistence
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    """In-memory database for MVP"""
    
    def __init__(self):
        self.documents = {}
        self.tasks = {}
        self.workflows = {}
    
    async def store_document(self, document) -> None:
        """Store a document"""
        self.documents[document.id] = document.dict()
    
    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get a document by ID"""
        return self.documents.get(document_id)
    
    async def get_documents(self, limit: int = 50) -> List[Dict]:
        """Get all documents"""
        docs = list(self.documents.values())
        # Sort by processed_time descending
        docs.sort(key=lambda x: x.get('processed_time', ''), reverse=True)
        return docs[:limit]
    
    async def store_task(self, task) -> None:
        """Store a task"""
        self.tasks[task.id] = task.dict()
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
    
    async def get_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get tasks with filters"""
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.get('status') == status]
        
        if priority:
            tasks = [t for t in tasks if t.get('priority') == priority]
        
        # Sort by created_at descending
        tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return tasks[:limit]
    
    async def update_task(self, task_id: str, updates: Dict) -> Optional[Dict]:
        """Update a task"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        task.update(updates)
        task['updated_at'] = datetime.utcnow().isoformat()
        
        self.tasks[task_id] = task
        return task
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
    
    async def store_workflow(self, workflow) -> None:
        """Store a workflow"""
        self.workflows[workflow.id] = workflow.dict()
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Get a workflow by ID"""
        return self.workflows.get(workflow_id)
    
    async def get_workflows(self, status: Optional[str] = None) -> List[Dict]:
        """Get workflows with filters"""
        workflows = list(self.workflows.values())
        
        if status:
            workflows = [w for w in workflows if w.get('status') == status]
        
        # Sort by created_at descending
        workflows.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return workflows
    
    async def get_stats(self) -> Dict:
        """Get system statistics"""
        total_tasks = len(self.tasks)
        total_workflows = len(self.workflows)
        total_documents = len(self.documents)
        
        tasks_by_status = {}
        for task in self.tasks.values():
            status = task.get('status', 'unknown')
            tasks_by_status[status] = tasks_by_status.get(status, 0) + 1
        
        return {
            "total_documents": total_documents,
            "total_tasks": total_tasks,
            "total_workflows": total_workflows,
            "tasks_by_status": tasks_by_status,
            "timestamp": datetime.utcnow().isoformat()
        }

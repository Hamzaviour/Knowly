import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Boolean
from app.database import Base

class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    trigger_type = Column(String(100), nullable=False) # document.uploaded, analysis.completed, schedule
    condition_rules = Column(JSON, default=dict) # e.g. {"file_type": "contract", "keywords": ["liability"]}
    actions = Column(JSON, default=list) # [{"type": "run_agent", "agent": "legal"}, {"type": "webhook", "url": "..."}]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    status = Column(String(50), default="pending") # pending, running, completed, failed
    trigger_payload = Column(JSON, default=dict)
    execution_result = Column(JSON, default=dict)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

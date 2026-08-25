from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.organization import Workspace
from app.models.knowledge_base import KnowledgeBase
import uuid

router = APIRouter(prefix="/workspaces", tags=["Workspaces & Knowledge Bases"])

@router.get("")
def list_workspaces(db: Session = Depends(get_db)):
    ws = db.query(Workspace).all()
    return [{"id": w.id, "name": w.name} for w in ws]

@router.get("/{workspace_id}/knowledge-bases")
def list_knowledge_bases(workspace_id: str, db: Session = Depends(get_db)):
    kbs = db.query(KnowledgeBase).filter(KnowledgeBase.workspace_id == workspace_id).all()
    return [{"id": k.id, "name": k.name, "description": k.description} for k in kbs]

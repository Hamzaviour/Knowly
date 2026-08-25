from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.workflow import Workflow
from app.schemas.api_schemas import WorkflowCreateRequest
import uuid

router = APIRouter(prefix="/workflows", tags=["Workflows & Automation"])

@router.post("")
def create_workflow(req: WorkflowCreateRequest, db: Session = Depends(get_db)):
    wf = Workflow(
        id=str(uuid.uuid4()),
        name=req.name,
        workspace_id=req.workspace_id,
        trigger_type=req.trigger_type,
        condition_rules=req.condition_rules,
        actions=req.actions
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return {"status": "created", "workflow_id": wf.id, "name": wf.name}

@router.get("")
def list_workflows(workspace_id: str = "default-workspace", db: Session = Depends(get_db)):
    wfs = db.query(Workflow).filter(Workflow.workspace_id == workspace_id).all()
    return [{"id": w.id, "name": w.name, "trigger": w.trigger_type, "is_active": w.is_active} for w in wfs]

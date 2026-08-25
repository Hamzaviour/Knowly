from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.document import Document
from app.models.chat import ChatMessage
from app.models.analytics import UsageMetric
from app.schemas.api_schemas import AnalyticsSummaryResponse

router = APIRouter(prefix="/analytics", tags=["Analytics & Cost"])

@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(workspace_id: str = "default-workspace", db: Session = Depends(get_db)):
    total_docs = db.query(Document).filter(Document.workspace_id == workspace_id).count()
    total_queries = db.query(ChatMessage).filter(ChatMessage.role == "user").count()
    
    metrics = db.query(UsageMetric).filter(UsageMetric.workspace_id == workspace_id).all()
    total_tokens = sum(m.total_tokens for m in metrics)
    total_cost = sum(m.estimated_cost_usd for m in metrics)
    avg_latency = (sum(m.latency_ms for m in metrics) / len(metrics)) if metrics else 120.0

    model_breakdown = {}
    for m in metrics:
        model_breakdown[m.model] = model_breakdown.get(m.model, 0) + m.total_tokens

    return AnalyticsSummaryResponse(
        total_documents=total_docs,
        total_queries=total_queries,
        total_tokens_used=total_tokens,
        total_estimated_cost_usd=round(total_cost, 4),
        avg_latency_ms=round(avg_latency, 2),
        model_breakdown=model_breakdown
    )

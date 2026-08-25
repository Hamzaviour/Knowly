from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.document import Document, DocumentChunk
from app.agents.deep_research import DeepResearchEngine
from app.agents.report_agent import ReportAgent
from app.schemas.api_schemas import DeepResearchRequest, DeepResearchResponse

router = APIRouter(prefix="/research", tags=["Deep Research"])

@router.post("", response_model=DeepResearchResponse)
def run_deep_research(req: DeepResearchRequest, db: Session = Depends(get_db)):
    chunks_records = db.query(DocumentChunk).join(Document).filter(Document.workspace_id == req.workspace_id).all()
    chunks_data = [{
        "chunk_id": c.id,
        "document_id": c.document_id,
        "document_title": c.document.title if c.document else "Doc",
        "content": c.content,
        "page_number": c.page_number,
        "section": c.section
    } for c in chunks_records]

    research_res = DeepResearchEngine.conduct_research(req.query, chunks_data)
    md_report = ReportAgent.generate_markdown_report(research_res)

    return DeepResearchResponse(
        research_title=research_res["research_title"],
        agenda=research_res["agenda"],
        executive_summary=research_res["executive_summary"],
        findings=research_res["findings"],
        contradictions=research_res["contradictions"],
        recommendations=research_res["recommendations"],
        markdown_report=md_report
    )

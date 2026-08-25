from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.document import Document
from app.agents.comparison_agent import DocumentComparisonAgent
from app.schemas.api_schemas import ComparisonRequest, ComparisonResponse

router = APIRouter(prefix="/compare", tags=["Document Comparison"])

@router.post("", response_model=ComparisonResponse)
def compare_documents(req: ComparisonRequest, db: Session = Depends(get_db)):
    doc1 = db.query(Document).filter(Document.id == req.doc1_id).first()
    doc2 = db.query(Document).filter(Document.id == req.doc2_id).first()
    
    if not doc1 or not doc2:
        raise HTTPException(status_code=404, detail="One or both documents not found")

    text1 = "\n".join([c.content for c in doc1.chunks]) if doc1.chunks else f"Content for {doc1.title}"
    text2 = "\n".join([c.content for c in doc2.chunks]) if doc2.chunks else f"Content for {doc2.title}"

    res = DocumentComparisonAgent.compare_documents(
        doc1_title=doc1.title,
        doc1_text=text1,
        doc2_title=doc2.title,
        doc2_text=text2
    )

    return ComparisonResponse(
        doc1_title=res["doc1_title"],
        doc2_title=res["doc2_title"],
        matrix=res["matrix"],
        changes_summary=res["changes_summary"],
        detailed_diff=res["detailed_diff"]
    )

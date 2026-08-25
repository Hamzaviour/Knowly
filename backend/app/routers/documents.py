from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.document import Document, DocumentChunk
from app.ingestion.parser_factory import DocumentParserFactory
from app.ingestion.chunker import LayoutAwareChunker
from app.ingestion.table_parser import TableIntelligenceEngine
from app.schemas.api_schemas import DocumentUploadResponse
from app.config import settings
import os
import uuid
import json

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: str = Form("default-workspace"),
    db: Session = Depends(get_db)
):
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    filename = file.filename or "uploaded_file"
    ext = os.path.splitext(filename)[1]
    saved_path = os.path.join(settings.STORAGE_DIR, f"{file_id}_{filename}")

    with open(saved_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Ingest and parse
    parsed = DocumentParserFactory.parse_file(saved_path)
    pages = parsed.get("pages", [])
    
    # Chunking
    chunker = LayoutAwareChunker()
    chunks_data = chunker.chunk_document(pages)

    # Save to database
    doc = Document(
        id=file_id,
        title=filename,
        file_type=parsed.get("file_type", "unknown"),
        file_path=saved_path,
        file_size=len(content),
        page_count=len(pages),
        doc_metadata=parsed.get("table_metadata", {}),
        workspace_id=workspace_id,
        is_processed=True,
        has_tables=parsed.get("is_tabular", False)
    )
    db.add(doc)

    for c in chunks_data:
        chunk = DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=file_id,
            chunk_index=c["chunk_index"],
            content=c["content"],
            page_number=c["page_number"],
            section=c["section"],
            char_start=c["char_start"],
            char_end=c["char_end"],
            bbox=c.get("bbox")
        )
        db.add(chunk)

    db.commit()
    db.refresh(doc)

    return DocumentUploadResponse(
        id=doc.id,
        title=doc.title,
        file_type=doc.file_type,
        file_size=doc.file_size,
        page_count=doc.page_count,
        chunks_count=len(chunks_data),
        has_tables=doc.has_tables,
        created_at=doc.created_at
    )

@router.get("")
def list_documents(workspace_id: str = "default-workspace", db: Session = Depends(get_db)):
    docs = db.query(Document).filter(Document.workspace_id == workspace_id).all()
    return [{
        "id": d.id,
        "title": d.title,
        "file_type": d.file_type,
        "page_count": d.page_count,
        "has_tables": d.has_tables,
        "created_at": d.created_at
    } for d in docs]

@router.post("/query-table")
def query_spreadsheet(doc_id: str, question: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc or not doc.has_tables:
        raise HTTPException(status_code=404, detail="Tabular document not found")
    
    # Auto-generate and run analytical logic
    code = """
numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
if numeric_cols:
    summary = df.describe().to_dict()
    result = {"summary": summary, "sample": df.head(5).to_dict(orient='records')}
else:
    result = df.head(10).to_dict(orient='records')
"""
    analysis = TableIntelligenceEngine.execute_analysis(doc.file_path, code)
    return {"doc_title": doc.title, "question": question, "result": analysis}

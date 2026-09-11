from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from app.database import get_db
from app.auth import get_optional_user
from app.models.document import Document, DocumentChunk, DocumentShare
from app.models.subscription import Subscription, PlanType, SubscriptionStatus
from app.models.user import User
from app.ingestion.parser_factory import DocumentParserFactory
from app.ingestion.chunker import LayoutAwareChunker
from app.ingestion.table_parser import TableIntelligenceEngine
from app.schemas.api_schemas import DocumentUploadResponse
from app.config import settings
import os
import uuid
import json
import re

router = APIRouter(prefix="/documents", tags=["Documents"])

def check_upload_limit(workspace_id: str, db: Session, user: Optional[User] = None):
    """
    Validates whether the workspace / user is allowed to upload more documents.
    Free plan: Max 5 documents
    Pro plan: Unlimited documents
    """
    # 1. Check if user or workspace has an active Pro subscription
    is_pro = False
    if user:
        sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        if sub and sub.plan_type in [PlanType.PRO, "pro"] and sub.status in [SubscriptionStatus.ACTIVE, "active"]:
            is_pro = True
    else:
        # Check global/default workspace subscription
        sub = db.query(Subscription).first()
        if sub and sub.plan_type in [PlanType.PRO, "pro"] and sub.status in [SubscriptionStatus.ACTIVE, "active"]:
            is_pro = True

    if is_pro:
        return True

    # 2. Count existing documents in this workspace
    current_count = db.query(Document).filter(Document.workspace_id == workspace_id).count()
    if current_count >= settings.FREE_PLAN_DOC_LIMIT:
        raise HTTPException(
            status_code=403,
            detail=f"Free plan upload limit reached (maximum {settings.FREE_PLAN_DOC_LIMIT} documents). Please upgrade to Pro for unlimited uploads."
        )
    return True

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: str = Form("default-workspace"),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    # Enforce Free Plan Upload Limit
    check_upload_limit(workspace_id=workspace_id, db=db, user=user)

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
def list_documents(
    workspace_id: str = "default-workspace",
    db: Session = Depends(get_db)
):
    docs = db.query(Document).filter(Document.workspace_id == workspace_id).all()
    return [{
        "id": d.id,
        "title": d.title,
        "file_type": d.file_type,
        "page_count": d.page_count,
        "has_tables": d.has_tables,
        "file_size": d.file_size or 0,
        "chunks_count": len(d.chunks) if d.chunks else 0,
        "shares_count": len(d.shares) if d.shares else 0,
        "shares": [{"id": s.id, "email": s.shared_with_email, "permission": s.permission, "created_at": s.created_at} for s in d.shares] if d.shares else [],
        "created_at": d.created_at
    } for d in docs]

@router.delete("/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter((Document.id == doc_id) | (Document.title == doc_id)).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 1. Clean up physical file
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    # 2. Delete KB links
    try:
        from app.models.knowledge_base import KBDocumentLink
        db.query(KBDocumentLink).filter(KBDocumentLink.document_id == doc.id).delete(synchronize_session=False)
    except Exception:
        pass

    # 3. Delete citations associated with chunks
    try:
        from app.models.document import Citation
        chunk_ids = [c.id for c in doc.chunks] if doc.chunks else []
        if chunk_ids:
            db.query(Citation).filter(Citation.chunk_id.in_(chunk_ids)).delete(synchronize_session=False)
    except Exception:
        pass

    # 4. Delete shares
    try:
        db.query(DocumentShare).filter(DocumentShare.document_id == doc.id).delete(synchronize_session=False)
    except Exception:
        pass

    # 5. Delete chunks
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete(synchronize_session=False)
    
    # 6. Delete document record
    db.delete(doc)
    db.commit()
    return {"status": "deleted", "id": doc_id, "title": doc.title}

# ==============================================================================
# Document Sharing Endpoints
# ==============================================================================

@router.post("/{doc_id}/share")
async def share_document(
    doc_id: str,
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter((Document.id == doc_id) | (Document.title == doc_id)).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    email = (payload.get("email") or "").strip().lower()
    permission = (payload.get("permission") or "viewer").lower()

    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email address is required to share this document.")

    if permission not in ["viewer", "editor", "admin"]:
        permission = "viewer"

    # Check if share already exists for this email
    existing_share = db.query(DocumentShare).filter(
        DocumentShare.document_id == doc.id,
        DocumentShare.shared_with_email == email
    ).first()

    if existing_share:
        existing_share.permission = permission
        db.commit()
        db.refresh(existing_share)
        return {
            "status": "updated",
            "share": {
                "id": existing_share.id,
                "document_id": doc.id,
                "document_title": doc.title,
                "shared_with_email": existing_share.shared_with_email,
                "permission": existing_share.permission,
                "created_at": existing_share.created_at
            }
        }

    new_share = DocumentShare(
        document_id=doc.id,
        shared_by_user_id=user.id if user else "workspace_admin",
        shared_with_email=email,
        permission=permission
    )
    db.add(new_share)
    db.commit()
    db.refresh(new_share)

    return {
        "status": "created",
        "share": {
            "id": new_share.id,
            "document_id": doc.id,
            "document_title": doc.title,
            "shared_with_email": new_share.shared_with_email,
            "permission": new_share.permission,
            "created_at": new_share.created_at
        }
    }

@router.get("/{doc_id}/shares")
def get_document_shares(
    doc_id: str,
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter((Document.id == doc_id) | (Document.title == doc_id)).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    shares = db.query(DocumentShare).filter(DocumentShare.document_id == doc.id).all()
    return [{
        "id": s.id,
        "document_id": s.document_id,
        "shared_with_email": s.shared_with_email,
        "permission": s.permission,
        "created_at": s.created_at
    } for s in shares]

@router.delete("/{doc_id}/shares/{share_id}")
def revoke_document_share(
    doc_id: str,
    share_id: str,
    db: Session = Depends(get_db)
):
    share = db.query(DocumentShare).filter(
        (DocumentShare.id == share_id) | (DocumentShare.shared_with_email == share_id)
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share permission not found")

    db.delete(share)
    db.commit()
    return {"status": "revoked", "share_id": share_id}

@router.get("/shared/with-me")
def list_shared_with_me(
    email: Optional[str] = Query(None),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    target_email = email or (user.email if user else None)
    if not target_email:
        return []

    shares = db.query(DocumentShare).filter(DocumentShare.shared_with_email == target_email.lower()).all()
    doc_ids = [s.document_id for s in shares]
    if not doc_ids:
        return []

    docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
    shares_by_doc = {s.document_id: s for s in shares}

    return [{
        "id": d.id,
        "title": d.title,
        "file_type": d.file_type,
        "page_count": d.page_count,
        "has_tables": d.has_tables,
        "file_size": d.file_size or 0,
        "permission": shares_by_doc[d.id].permission if d.id in shares_by_doc else "viewer",
        "shared_at": shares_by_doc[d.id].created_at if d.id in shares_by_doc else None,
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

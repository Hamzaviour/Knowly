from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.document import Document, DocumentChunk
from app.models.chat import ChatSession, ChatMessage
from app.models.analytics import UsageMetric
from app.schemas.api_schemas import ChatRequest, ChatResponse
from app.agents.orchestrator import AgentOrchestrator
import uuid

router = APIRouter(prefix="/chat", tags=["Chat & Agents"])

@router.post("", response_model=ChatResponse)
async def chat_with_workspace(req: ChatRequest, db: Session = Depends(get_db)):
    # 1. Fetch chunks for workspace / knowledge bases
    chunks_query = db.query(DocumentChunk).join(Document).filter(Document.workspace_id == req.workspace_id)
    chunks_records = chunks_query.all()
    
    chunks_data = []
    for c in chunks_records:
        chunks_data.append({
            "chunk_id": c.id,
            "document_id": c.document_id,
            "document_title": c.document.title if c.document else "Doc",
            "content": c.content,
            "page_number": c.page_number,
            "section": c.section,
            "char_start": c.char_start,
            "char_end": c.char_end,
            "bbox": c.bbox
        })

    # 2. Get or create session
    session_id = req.session_id or str(uuid.uuid4())
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        session = ChatSession(id=session_id, workspace_id=req.workspace_id, mode=req.mode)
        db.add(session)
        db.commit()

    # 3. Load conversation history for multi-turn context (last 10 exchanges = 20 messages)
    prior_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .limit(20)
        .all()
    )
    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in prior_messages
    ]

    # 4. Process via AI Orchestrator (with history for multi-turn follow-ups)
    orchestration_result = await AgentOrchestrator.process_request(
        query=req.query,
        mode=req.mode,
        document_chunks=chunks_data,
        api_keys=req.api_keys,
        conversation_history=conversation_history
    )

    answer_text = orchestration_result.get("answer", "")
    citations = orchestration_result.get("citations", [])
    model_used = orchestration_result.get("model_used", "openai/gpt-4o")
    tokens = orchestration_result.get("tokens", {})
    cost = orchestration_result.get("cost_usd", 0.0)

    # 5. Record messages and metrics
    msg_user = ChatMessage(session_id=session_id, role="user", content=req.query)
    msg_ai = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=answer_text,
        citations=citations,
        model_used=model_used
    )
    metric = UsageMetric(
        workspace_id=req.workspace_id,
        request_type="chat",
        model=model_used,
        prompt_tokens=tokens.get("prompt_tokens", 0),
        completion_tokens=tokens.get("completion_tokens", 0),
        total_tokens=tokens.get("total_tokens", 0),
        estimated_cost_usd=cost
    )
    db.add_all([msg_user, msg_ai, metric])
    db.commit()

    return ChatResponse(
        answer=answer_text,
        session_id=session_id,
        mode=req.mode,
        citations=citations,
        model_used=model_used,
        tokens=tokens,
        cost_usd=cost
    )

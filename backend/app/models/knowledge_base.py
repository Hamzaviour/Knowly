import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    workspace = relationship("Workspace", back_populates="knowledge_bases")
    documents = relationship("KBDocumentLink", back_populates="knowledge_base", cascade="all, delete-orphan")

class KBDocumentLink(Base):
    __tablename__ = "kb_document_links"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    document = relationship("Document", back_populates="kb_links")

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False) # pdf, docx, xlsx, pptx, image, scanned_pdf
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    page_count = Column(Integer, default=1)
    doc_metadata = Column(JSON, default=dict)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    is_processed = Column(Boolean, default=False)
    has_tables = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    workspace = relationship("Workspace", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    kb_links = relationship("KBDocumentLink", back_populates="document", cascade="all, delete-orphan")
    shares = relationship("DocumentShare", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, default=1)
    section = Column(String(255), nullable=True)
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)
    bbox = Column(JSON, nullable=True) # [x0, y0, x1, y1] for highlighting
    chunk_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="chunks")
    citations = relationship("Citation", back_populates="chunk", cascade="all, delete-orphan")

class Citation(Base):
    __tablename__ = "citations"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chunk_id = Column(String(36), ForeignKey("document_chunks.id"), nullable=False)
    quote = Column(Text, nullable=False)
    source_title = Column(String(255), nullable=False)
    page_number = Column(Integer, nullable=False)
    section = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    chunk = relationship("DocumentChunk", back_populates="citations")

class DocumentShare(Base):
    __tablename__ = "document_shares"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    shared_by_user_id = Column(String(36), nullable=True)
    shared_with_email = Column(String(255), nullable=False, index=True)
    permission = Column(String(50), default="viewer", nullable=False) # viewer, editor, admin
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="shares")

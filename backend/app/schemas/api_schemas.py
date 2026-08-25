from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    id: str
    title: str
    file_type: str
    file_size: int
    page_count: int
    chunks_count: int
    has_tables: bool
    created_at: datetime

class ChatRequest(BaseModel):
    query: str
    workspace_id: str
    session_id: Optional[str] = None
    mode: str = "standard" # standard, deep_research, compare, analyst
    knowledge_base_ids: Optional[List[str]] = None

class CitationSchema(BaseModel):
    citation_id: Optional[str] = None
    document_id: Optional[str] = None
    document_title: str
    page_number: int
    section: Optional[str] = None
    quote_snippet: str
    badge: str

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    mode: str
    citations: List[CitationSchema] = []
    model_used: str
    tokens: Dict[str, int] = {}
    cost_usd: float = 0.0

class ComparisonRequest(BaseModel):
    doc1_id: str
    doc2_id: str
    workspace_id: str

class ComparisonResponse(BaseModel):
    doc1_title: str
    doc2_title: str
    matrix: List[Dict[str, Any]]
    changes_summary: Dict[str, Any]
    detailed_diff: Dict[str, Any]

class DeepResearchRequest(BaseModel):
    query: str
    workspace_id: str
    knowledge_base_ids: Optional[List[str]] = None

class DeepResearchResponse(BaseModel):
    research_title: str
    agenda: List[str]
    executive_summary: str
    findings: List[Dict[str, Any]]
    contradictions: List[str]
    recommendations: List[str]
    markdown_report: str

class WorkflowCreateRequest(BaseModel):
    name: str
    workspace_id: str
    trigger_type: str
    condition_rules: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)

class AnalyticsSummaryResponse(BaseModel):
    total_documents: int
    total_queries: int
    total_tokens_used: int
    total_estimated_cost_usd: float
    avg_latency_ms: float
    model_breakdown: Dict[str, int]


class EnqueueTaskRequest(BaseModel):
    name: str
    task_type: str  # workflow, webhook, cleanup
    payload: Dict[str, Any] = Field(default_factory=dict)
    run_at: Optional[str] = None
    max_retries: int = 3


class ScheduleCronRequest(BaseModel):
    workflow_id: str
    cron_expr: str
    name: str = ""


class ScheduleIntervalRequest(BaseModel):
    workflow_id: str
    seconds: int
    name: str = ""

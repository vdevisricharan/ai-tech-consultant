from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SourceItem(BaseModel):
    title: str
    url: str
    heading: str = ""
    relevance: float = 0.0
    image_refs: List[str] = Field(default_factory=list)

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    model: Optional[str] = "claude-3-5-sonnet-20241022"

class QueryResponse(BaseModel):
    answer: str
    status: str = Field(..., description="'answered' or 'insufficient_evidence'")
    sources: List[SourceItem] = Field(default_factory=list)
    confidence: float = 0.0
    needs_human: bool = False
    tokens_used: Optional[int] = 0
    latency_ms: Optional[float] = 0.0

class EscalationCreate(BaseModel):
    question: str
    context: Optional[str] = ""
    reason: str

class EscalationResolve(BaseModel):
    expert_answer: str

class EscalationRecord(BaseModel):
    id: int
    question: str
    context: Optional[str] = ""
    reason: str
    status: str
    expert_answer: Optional[str] = None
    created_at: str
    resolved_at: Optional[str] = None

class IngestionRunRequest(BaseModel):
    limit: Optional[int] = 50
    force_rescrape: bool = False

class IngestionStatusResponse(BaseModel):
    total_articles: int
    indexed: int
    new: int
    modified: int
    failed: int
    deleted: int
    total_chunks: int
    pending_escalations: int

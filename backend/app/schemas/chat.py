from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any

class AskQuestionRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    conversation_id: Optional[str] = None

class CitationItem(BaseModel):
    citation_id: str
    document_id: str
    document_filename: str
    chunk_id: str
    location: str
    excerpt: str
    score: float = 1.0

class ClaimVerificationItem(BaseModel):
    claim_text: str
    status: str  # supported, partially_supported, contradicted, insufficient_evidence
    supporting_evidence_ids: List[str] = []
    contradicting_evidence_ids: List[str] = []
    explanation: str
    confidence_notes: str = ""

class ConflictItem(BaseModel):
    id: Optional[str] = None
    subject: str
    relationship_type: str  # supports, contradicts, supersedes, qualifies
    conflict_category: str  # factual_disagreement, outdated_policy, exception_clause, differing_scope
    source_a_name: str
    source_a_location: str
    source_a_excerpt: str
    source_b_name: str
    source_b_location: str
    source_b_excerpt: str
    explanation: str

class ChatResponse(BaseModel):
    message_id: str
    conversation_id: str
    role: str = "assistant"
    content: str
    verification_status: str  # supported, partially_supported, contradicted, insufficient_evidence
    citations: List[CitationItem] = []
    claims_verification: List[ClaimVerificationItem] = []
    conflicts_detected: List[ConflictItem] = []
    uncertainty_notes: Optional[str] = None
    created_at: datetime

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    verification_status: str
    citations: List[CitationItem] = []
    claims_verification: List[ClaimVerificationItem] = []
    conflicts_detected: List[ConflictItem] = []
    uncertainty_notes: Optional[str] = None
    created_at: datetime

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages_count: Optional[int] = 0

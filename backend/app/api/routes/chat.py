import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import (
    AskQuestionRequest,
    ChatResponse,
    ConversationResponse,
    MessageResponse,
    CitationItem,
    ClaimVerificationItem,
    ConflictItem
)
from app.api.dependencies import get_current_active_user
from app.services.retrieval_service import RetrievalService
from app.services.conflict_service import ConflictService
from app.services.answer_service import get_llm_provider
from app.services.verification_service import VerificationService
from app.services.audit_service import log_audit_event

router = APIRouter(tags=["Research & Chat"])

@router.post("/chat/ask", response_model=ChatResponse)
def ask_question(
    req: AskQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 1. Manage Conversation
    conv = None
    if req.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == req.conversation_id,
            Conversation.user_id == current_user.id
        ).first()

    if not conv:
        # Title from first 6 words of question
        title_words = req.question.strip().split()[:6]
        title = " ".join(title_words) or "Research Query"
        conv = Conversation(user_id=current_user.id, title=title)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Save User message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=req.question,
        citations_json="[]",
        verification_status="not_applicable",
        verification_details_json="{}",
        conflicts_detected_json="[]"
    )
    db.add(user_msg)
    db.commit()

    # 2. Hybrid Retrieval (Authorized chunks only)
    retriever = RetrievalService(top_k=8)
    passages = retriever.hybrid_search(db, user_id=current_user.id, query=req.question)

    # 3. Conflict Detection
    candidate_conflicts = ConflictService.detect_conflicts_in_passages(passages)
    persisted_conflicts = ConflictService.persist_detected_conflicts(db, current_user.id, candidate_conflicts)
    
    conflict_items = [
        ConflictItem(
            id=c.id,
            subject=c.subject,
            relationship_type=c.relationship_type,
            conflict_category=c.conflict_category,
            source_a_name=c.source_a_name,
            source_a_location=c.source_a_location,
            source_a_excerpt=c.source_a_excerpt,
            source_b_name=c.source_b_name,
            source_b_location=c.source_b_location,
            source_b_excerpt=c.source_b_excerpt,
            explanation=c.explanation
        )
        for c in persisted_conflicts
    ]

    # 4. Answer Generation via LLM Provider
    llm = get_llm_provider()
    candidate_answer = llm.generate(req.question, passages)

    # 5. Claim-level Verification & Abstention
    verification = VerificationService.verify_answer(candidate_answer, passages)

    # 6. Save Assistant message
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=verification.final_answer,
        citations_json=json.dumps([c.model_dump() for c in verification.valid_citations]),
        verification_status=verification.overall_status,
        verification_details_json=json.dumps([cv.model_dump() for cv in verification.verified_claims]),
        conflicts_detected_json=json.dumps([cf.model_dump() for cf in conflict_items]),
        uncertainty_notes=verification.uncertainty_notes
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    log_audit_event(
        db,
        action="QUERY_ASKED",
        target_type="CONVERSATION",
        actor_id=current_user.id,
        target_id=conv.id,
        details={"question_len": len(req.question), "status": verification.overall_status}
    )

    return ChatResponse(
        message_id=assistant_msg.id,
        conversation_id=conv.id,
        role="assistant",
        content=assistant_msg.content,
        verification_status=assistant_msg.verification_status,
        citations=verification.valid_citations,
        claims_verification=verification.verified_claims,
        conflicts_detected=conflict_items,
        uncertainty_notes=assistant_msg.uncertainty_notes,
        created_at=assistant_msg.created_at
    )


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    convs = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()

    results = []
    for c in convs:
        m_count = db.query(Message).filter(Message.conversation_id == c.id).count()
        results.append(ConversationResponse(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            messages_count=m_count
        ))
    return results


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    m_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages_count=m_count
    )


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    msgs = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.asc()).all()
    results = []
    for m in msgs:
        cits = [CitationItem(**c) for c in json.loads(m.citations_json or "[]")]
        claims = [ClaimVerificationItem(**c) for c in json.loads(m.verification_details_json or "[]")]
        confs = [ConflictItem(**c) for c in json.loads(m.conflicts_detected_json or "[]")]
        results.append(MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            verification_status=m.verification_status,
            citations=cits,
            claims_verification=claims,
            conflicts_detected=confs,
            uncertainty_notes=m.uncertainty_notes,
            created_at=m.created_at
        ))
    return results

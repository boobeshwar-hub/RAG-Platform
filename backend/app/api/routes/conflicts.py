from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.conflict import Conflict
from app.schemas.conflict import ConflictResponse, ConflictReviewUpdate
from app.api.dependencies import get_current_active_user
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/conflicts", tags=["Conflicts"])

@router.get("", response_model=List[ConflictResponse])
def list_conflicts(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Conflict).filter(Conflict.user_id == current_user.id)
    if status_filter:
        query = query.filter(Conflict.review_status == status_filter)
    
    return query.order_by(Conflict.created_at.desc()).all()


@router.get("/{conflict_id}", response_model=ConflictResponse)
def get_conflict(
    conflict_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    conflict = db.query(Conflict).filter(
        Conflict.id == conflict_id,
        Conflict.user_id == current_user.id
    ).first()
    if not conflict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conflict not found")
    return conflict


@router.patch("/{conflict_id}/review", response_model=ConflictResponse)
def review_conflict(
    conflict_id: str,
    update: ConflictReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    conflict = db.query(Conflict).filter(
        Conflict.id == conflict_id,
        Conflict.user_id == current_user.id
    ).first()
    if not conflict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conflict not found")

    conflict.review_status = update.review_status
    conflict.reviewed_at = datetime.now(timezone.utc)
    conflict.reviewed_by_id = current_user.id
    db.commit()
    db.refresh(conflict)

    log_audit_event(
        db,
        action="CONFLICT_REVIEWED",
        target_type="CONFLICT",
        actor_id=current_user.id,
        target_id=conflict.id,
        details={"status": update.review_status}
    )
    return conflict

import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.schemas.evidence import EvidenceDetailResponse
from app.api.dependencies import get_current_active_user

router = APIRouter(prefix="/evidence", tags=["Evidence"])

@router.get("/{evidence_id}", response_model=EvidenceDetailResponse)
def get_evidence_details(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == evidence_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence passage not found")

    doc = db.query(Document).filter(
        Document.id == chunk.document_id,
        Document.owner_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view evidence from this document"
        )

    meta = {}
    if chunk.metadata_json:
        try:
            meta = json.loads(chunk.metadata_json)
        except Exception:
            pass

    return EvidenceDetailResponse(
        id=chunk.id,
        document_id=doc.id,
        document_filename=doc.original_filename,
        chunk_index=chunk.chunk_index,
        text=chunk.text,
        page_or_sheet_location=chunk.page_or_sheet_location,
        metadata=meta,
        created_at=chunk.created_at
    )

from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.api.dependencies import get_current_active_user
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    doc = DocumentService.save_and_create_document(db, file, current_user.id)
    chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
    
    return DocumentResponse(
        id=doc.id,
        owner_id=doc.owner_id,
        original_filename=doc.original_filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        checksum_sha256=doc.checksum_sha256,
        processing_status=doc.processing_status,
        processing_error=doc.processing_error,
        chunks_count=chunks_count,
        upload_timestamp=doc.upload_timestamp
    )


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    docs = db.query(Document).filter(Document.owner_id == current_user.id).order_by(Document.upload_timestamp.desc()).all()
    results = []
    for doc in docs:
        c_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
        results.append(DocumentResponse(
            id=doc.id,
            owner_id=doc.owner_id,
            original_filename=doc.original_filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            checksum_sha256=doc.checksum_sha256,
            processing_status=doc.processing_status,
            processing_error=doc.processing_error,
            chunks_count=c_count,
            upload_timestamp=doc.upload_timestamp
        ))
    return results


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    c_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
    return DocumentResponse(
        id=doc.id,
        owner_id=doc.owner_id,
        original_filename=doc.original_filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        checksum_sha256=doc.checksum_sha256,
        processing_status=doc.processing_status,
        processing_error=doc.processing_error,
        chunks_count=c_count,
        upload_timestamp=doc.upload_timestamp
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    c_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
    return DocumentStatusResponse(
        id=doc.id,
        processing_status=doc.processing_status,
        processing_error=doc.processing_error,
        chunks_count=c_count,
        upload_timestamp=doc.upload_timestamp
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    deleted = DocumentService.delete_document(db, document_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found or unauthorized")
    return None

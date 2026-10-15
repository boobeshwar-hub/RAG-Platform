import os
import hashlib
import json
import shutil
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.models.claim import Claim
from app.models.conflict import Conflict
from app.services.extraction_service import ExtractionService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import get_embedding_provider
from app.services.audit_service import log_audit_event

class DocumentService:
    @staticmethod
    def calculate_checksum(file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                sha256.update(block)
        return sha256.hexdigest()

    @classmethod
    def save_and_create_document(
        cls,
        db: Session,
        upload_file: UploadFile,
        user_id: str
    ) -> Document:
        filename = upload_file.filename or "unknown_file"
        ext = os.path.splitext(filename)[1].lower()

        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{upload_file.filename}")

        # Stream save file to disk with size check
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        file_size = 0
        with open(temp_path, "wb") as buffer:
            while chunk := upload_file.file.read(65536):
                file_size += len(chunk)
                if file_size > max_bytes:
                    os.remove(temp_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
                    )
                buffer.write(chunk)

        checksum = cls.calculate_checksum(temp_path)

        # Check duplicate for the same user
        existing_doc = db.query(Document).filter(
            Document.owner_id == user_id,
            Document.checksum_sha256 == checksum
        ).first()

        if existing_doc and existing_doc.processing_status == "completed":
            os.remove(temp_path)
            return existing_doc

        storage_filename = f"{user_id}_{checksum[:12]}_{filename}"
        permanent_path = os.path.join(settings.UPLOAD_DIR, storage_filename)
        shutil.move(temp_path, permanent_path)

        doc = Document(
            owner_id=user_id,
            original_filename=filename,
            storage_key=permanent_path,
            file_type=ext.replace(".", ""),
            file_size=file_size,
            checksum_sha256=checksum,
            processing_status="pending",
            metadata_json=json.dumps({"original_filename": filename, "extension": ext})
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        log_audit_event(
            db,
            action="DOCUMENT_UPLOAD",
            target_type="DOCUMENT",
            actor_id=user_id,
            target_id=doc.id,
            details={"filename": filename, "file_size": file_size, "checksum": checksum}
        )

        # Process document
        cls.process_document_pipeline(db, doc.id)
        db.refresh(doc)
        return doc

    @classmethod
    def process_document_pipeline(cls, db: Session, document_id: str) -> None:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        doc.processing_status = "processing"
        doc.processing_error = None
        db.commit()

        try:
            # 1. Extraction
            extraction_result = ExtractionService.extract(doc.storage_key, doc.file_type)
            if not extraction_result.sections:
                doc.processing_status = "failed"
                doc.processing_error = "No readable content extracted from document."
                db.commit()
                return

            # 2. Chunking
            chunker = ChunkingService(target_chunk_size=400, chunk_overlap=60)
            chunks = chunker.chunk_sections(extraction_result.sections)

            if not chunks:
                doc.processing_status = "failed"
                doc.processing_error = "Could not generate passage chunks from extracted content."
                db.commit()
                return

            # 3. Embedding generation
            embedding_provider = get_embedding_provider()
            chunk_texts = [c.text for c in chunks]
            vectors = embedding_provider.get_embeddings(chunk_texts)

            # 4. Persistence
            for c_payload, vec in zip(chunks, vectors):
                chunk_entry = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=c_payload.chunk_index,
                    text=c_payload.text,
                    page_or_sheet_location=c_payload.location,
                    metadata_json=json.dumps(c_payload.metadata),
                    embedding=vec
                )
                db.add(chunk_entry)

            # Store updated document metadata
            doc_meta = json.loads(doc.metadata_json or "{}")
            doc_meta.update(extraction_result.format_metadata)
            doc_meta["total_chunks"] = len(chunks)
            doc.metadata_json = json.dumps(doc_meta)
            doc.processing_status = "completed"
            db.commit()

            logger.info(f"Successfully processed document {doc.id} ({doc.original_filename}): {len(chunks)} chunks created.")

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
            doc.processing_status = "failed"
            doc.processing_error = str(e)
            db.commit()

    @staticmethod
    def delete_document(db: Session, document_id: str, user_id: str) -> bool:
        doc = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == user_id
        ).first()

        if not doc:
            return False

        # Remove physical file if it exists
        if doc.storage_key and os.path.exists(doc.storage_key):
            try:
                os.remove(doc.storage_key)
            except Exception as e:
                logger.warning(f"Could not remove physical file {doc.storage_key}: {e}")

        # Cascade deletion handles chunks & claims in DB
        db.delete(doc)
        db.commit()

        log_audit_event(
            db,
            action="DOCUMENT_DELETE",
            target_type="DOCUMENT",
            actor_id=user_id,
            target_id=document_id,
            details={"original_filename": doc.original_filename}
        )
        return True

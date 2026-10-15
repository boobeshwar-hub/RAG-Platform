import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    storage_key = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, csv, xlsx
    file_size = Column(Integer, nullable=False)
    checksum_sha256 = Column(String(64), nullable=False, index=True)
    processing_status = Column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    metadata_json = Column(Text, default="{}", nullable=False)
    upload_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    owner = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", passive_deletes=True)
    claims = relationship("Claim", back_populates="document", cascade="all, delete-orphan", passive_deletes=True)

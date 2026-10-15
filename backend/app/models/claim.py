import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Claim(Base):
    __tablename__ = "claims"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(36), ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True, index=True)
    claim_text = Column(Text, nullable=False)
    subject = Column(String(255), nullable=False, index=True)
    property = Column(String(255), nullable=False)
    context_date = Column(String(100), nullable=True)
    context_scope = Column(String(255), nullable=True)
    source_authority = Column(String(100), nullable=True)
    status = Column(String(50), default="extracted", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="claims")
    chunk = relationship("DocumentChunk", back_populates="claims")

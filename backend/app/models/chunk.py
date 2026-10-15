import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.base import VectorType

def generate_uuid() -> str:
    return str(uuid.uuid4())

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    page_or_sheet_location = Column(String(150), nullable=False, default="Passage 1")
    metadata_json = Column(Text, default="{}", nullable=False)
    embedding = Column(VectorType, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="chunks")
    claims = relationship("Claim", back_populates="chunk")

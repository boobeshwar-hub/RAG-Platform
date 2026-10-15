import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    citations_json = Column(Text, default="[]", nullable=False)
    verification_status = Column(String(50), default="supported", nullable=False)  # supported, partially_supported, contradicted, insufficient_evidence
    verification_details_json = Column(Text, default="{}", nullable=False)
    conflicts_detected_json = Column(Text, default="[]", nullable=False)
    uncertainty_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    conversation = relationship("Conversation", back_populates="messages")

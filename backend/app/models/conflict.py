import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Conflict(Base):
    __tablename__ = "conflicts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(255), nullable=False, index=True)
    claim_a_id = Column(String(36), ForeignKey("claims.id", ondelete="SET NULL"), nullable=True)
    claim_b_id = Column(String(36), ForeignKey("claims.id", ondelete="SET NULL"), nullable=True)
    relationship_type = Column(String(50), default="contradicts", nullable=False)  # supports, contradicts, supersedes, qualifies
    conflict_category = Column(String(100), default="factual_disagreement", nullable=False) # factual_disagreement, outdated_policy, exception_clause, differing_scope
    source_a_name = Column(String(255), nullable=False)
    source_a_location = Column(String(150), nullable=False)
    source_a_excerpt = Column(Text, nullable=False)
    source_b_name = Column(String(255), nullable=False)
    source_b_location = Column(String(150), nullable=False)
    source_b_excerpt = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    review_status = Column(String(50), default="unresolved", nullable=False)  # unresolved, reviewed, resolved
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", foreign_keys=[user_id], back_populates="conflicts")
    reviewer = relationship("User", foreign_keys=[reviewed_by_id])

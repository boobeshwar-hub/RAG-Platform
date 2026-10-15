from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class ConflictReviewUpdate(BaseModel):
    review_status: str  # unresolved, reviewed, resolved

class ConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    subject: str
    relationship_type: str
    conflict_category: str
    source_a_name: str
    source_a_location: str
    source_a_excerpt: str
    source_b_name: str
    source_b_location: str
    source_b_excerpt: str
    explanation: str
    review_status: str
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

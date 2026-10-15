from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional
from datetime import datetime

class EvidenceDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    document_id: str
    document_filename: str
    chunk_index: int
    text: str
    page_or_sheet_location: str
    metadata: Dict[str, Any] = {}
    created_at: datetime

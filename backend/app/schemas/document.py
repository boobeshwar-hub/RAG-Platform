from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any

class DocumentChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    chunk_index: int
    text: str
    page_or_sheet_location: str
    metadata: Dict[str, Any] = {}
    created_at: datetime

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    owner_id: str
    original_filename: str
    file_type: str
    file_size: int
    checksum_sha256: str
    processing_status: str
    processing_error: Optional[str] = None
    chunks_count: Optional[int] = 0
    upload_timestamp: datetime

class DocumentStatusResponse(BaseModel):
    id: str
    processing_status: str
    processing_error: Optional[str] = None
    chunks_count: int
    upload_timestamp: datetime

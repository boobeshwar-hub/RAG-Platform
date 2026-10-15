from typing import List, Dict, Any
from pydantic import BaseModel
from app.services.extraction_service import ExtractedSection

class ChunkPayload(BaseModel):
    chunk_index: int
    text: str
    location: str
    metadata: Dict[str, Any] = {}

class ChunkingService:
    def __init__(self, target_chunk_size: int = 500, chunk_overlap: int = 80):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_sections(self, sections: List[ExtractedSection]) -> List[ChunkPayload]:
        chunks: List[ChunkPayload] = []
        chunk_idx = 1

        for sec in sections:
            text = sec.text.strip()
            if not text:
                continue

            # If section text is smaller than target_chunk_size, keep it intact to preserve full context
            if len(text) <= self.target_chunk_size:
                chunks.append(ChunkPayload(
                    chunk_index=chunk_idx,
                    text=text,
                    location=sec.location,
                    metadata=sec.metadata
                ))
                chunk_idx += 1
                continue

            # Split by sentences or paragraph markers
            words = text.split()
            current_words: List[str] = []
            current_len = 0

            for word in words:
                current_words.append(word)
                current_len += len(word) + 1
                if current_len >= self.target_chunk_size:
                    chunk_text = " ".join(current_words)
                    chunks.append(ChunkPayload(
                        chunk_index=chunk_idx,
                        text=chunk_text,
                        location=sec.location,
                        metadata=sec.metadata
                    ))
                    chunk_idx += 1
                    
                    # Compute overlap words
                    overlap_words = []
                    overlap_len = 0
                    for w in reversed(current_words):
                        overlap_words.insert(0, w)
                        overlap_len += len(w) + 1
                        if overlap_len >= self.chunk_overlap:
                            break
                    current_words = overlap_words
                    current_len = sum(len(w) + 1 for w in current_words)

            if current_words:
                chunk_text = " ".join(current_words)
                # Avoid tiny duplicate remainder
                if not chunks or chunk_text != chunks[-1].text:
                    chunks.append(ChunkPayload(
                        chunk_index=chunk_idx,
                        text=chunk_text,
                        location=sec.location,
                        metadata=sec.metadata
                    ))
                    chunk_idx += 1

        return chunks

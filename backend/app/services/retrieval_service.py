import math
import json
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from app.core.config import settings
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.services.embedding_service import get_embedding_provider

class RetrievedPassage(BaseModel):
    chunk_id: str
    document_id: str
    document_filename: str
    excerpt: str
    location: str
    score: float
    keyword_rank: Optional_Rank = None
    vector_rank: Optional_Rank = None
    metadata: Dict[str, Any] = {}

Optional_Rank = int | None

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

class RetrievalService:
    def __init__(self, top_k: int = 8, rrf_k: int = 60):
        self.top_k = top_k
        self.rrf_k = rrf_k
        self.embedding_provider = get_embedding_provider()

    def keyword_search(
        self,
        db: Session,
        user_id: str,
        query: str,
        limit: int = 20
    ) -> List[Tuple[DocumentChunk, Document, float]]:
        """
        Executes keyword search across authorized documents.
        Uses PostgreSQL full-text search when available, or token-overlap matching on SQLite.
        """
        terms = [t.lower() for t in query.split() if len(t) > 2]
        if not terms:
            terms = [query.lower()]

        # PostgreSQL native full-text search
        if settings.is_postgres:
            try:
                raw_sql = text("""
                    SELECT c.id, c.document_id, c.chunk_index, c.text, c.page_or_sheet_location, c.metadata_json,
                           ts_rank_cd(to_tsvector('english', c.text), plainto_tsquery('english', :q)) AS rank
                    FROM document_chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE d.owner_id = :user_id AND d.processing_status = 'completed'
                      AND to_tsvector('english', c.text) @@ plainto_tsquery('english', :q)
                    ORDER BY rank DESC
                    LIMIT :limit
                """)
                res = db.execute(raw_sql, {"q": query, "user_id": user_id, "limit": limit}).fetchall()
                results = []
                for row in res:
                    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == row[0]).first()
                    doc = db.query(Document).filter(Document.id == chunk.document_id).first()
                    if chunk and doc:
                        results.append((chunk, doc, float(row[6])))
                return results
            except Exception:
                pass  # Fall through to standard token match if tsvector extension is not configured

        # Universal fallback keyword search
        query_chunks = (
            db.query(DocumentChunk, Document)
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(
                Document.owner_id == user_id,
                Document.processing_status == "completed"
            )
            .all()
        )

        ranked = []
        for chunk, doc in query_chunks:
            chunk_lower = chunk.text.lower()
            score = 0.0
            # Term frequency and multi-word overlap
            for term in terms:
                if term in chunk_lower:
                    score += 1.0 + chunk_lower.count(term) * 0.2
            if query.lower() in chunk_lower:
                score += 3.0  # Exact phrase bonus
            
            if score > 0:
                ranked.append((chunk, doc, score))

        ranked.sort(key=lambda x: x[2], reverse=True)
        return ranked[:limit]

    def semantic_search(
        self,
        db: Session,
        user_id: str,
        query: str,
        limit: int = 20
    ) -> List[Tuple[DocumentChunk, Document, float]]:
        """
        Executes semantic search using vector cosine similarity on authorized documents.
        """
        query_vector = self.embedding_provider.get_embedding(query)
        if not query_vector:
            return []

        # Fetch chunks from user's completed documents
        chunks_with_doc = (
            db.query(DocumentChunk, Document)
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(
                Document.owner_id == user_id,
                Document.processing_status == "completed"
            )
            .all()
        )

        scored = []
        for chunk, doc in chunks_with_doc:
            emb = chunk.embedding
            if not emb:
                continue
            if isinstance(emb, str):
                try:
                    emb = json.loads(emb)
                except Exception:
                    continue
            sim = cosine_similarity(query_vector, emb)
            scored.append((chunk, doc, sim))

        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:limit]

    def hybrid_search(
        self,
        db: Session,
        user_id: str,
        query: str
    ) -> List[RetrievedPassage]:
        """
        Hybrid search using Reciprocal Rank Fusion (RRF).
        RRF Score = 1 / (k + rank_keyword) + 1 / (k + rank_semantic)
        """
        keyword_results = self.keyword_search(db, user_id, query, limit=30)
        semantic_results = self.semantic_search(db, user_id, query, limit=30)

        scores: Dict[str, float] = {}
        data_map: Dict[str, Tuple[DocumentChunk, Document]] = {}
        keyword_ranks: Dict[str, int] = {}
        vector_ranks: Dict[str, int] = {}

        # Process keyword ranks
        for rank, (chunk, doc, _) in enumerate(keyword_results, 1):
            cid = chunk.id
            data_map[cid] = (chunk, doc)
            keyword_ranks[cid] = rank
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))

        # Process vector ranks
        for rank, (chunk, doc, _) in enumerate(semantic_results, 1):
            cid = chunk.id
            data_map[cid] = (chunk, doc)
            vector_ranks[cid] = rank
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))

        # Sort by fused score
        sorted_chunks = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:self.top_k]

        passages: List[RetrievedPassage] = []
        for cid, score in sorted_chunks:
            chunk, doc = data_map[cid]
            meta = {}
            if chunk.metadata_json:
                try:
                    meta = json.loads(chunk.metadata_json)
                except Exception:
                    pass

            passages.append(RetrievedPassage(
                chunk_id=chunk.id,
                document_id=doc.id,
                document_filename=doc.original_filename,
                excerpt=chunk.text,
                location=chunk.page_or_sheet_location,
                score=round(score * 100, 3),
                keyword_rank=keyword_ranks.get(cid),
                vector_rank=vector_ranks.get(cid),
                metadata=meta
            ))

        return passages

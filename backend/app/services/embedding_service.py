import math
import hashlib
import json
from typing import List
from app.core.config import settings
from app.core.logging import logger

class EmbeddingProvider:
    def get_embedding(self, text: str) -> List[float]:
        raise NotImplementedError

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self.get_embedding(t) for t in texts]


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic, offline 384-dimensional embedding generator.
    Uses n-gram hashing and word-frequency projections with L2 normalization
    so semantically related phrases have high cosine similarity.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim

    def get_embedding(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        if not text:
            return vec
        
        words = text.lower().replace(",", " ").replace(".", " ").split()
        for i, word in enumerate(words):
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
            vec[idx] += sign * (1.0 + 1.0 / (i + 1))
            
            # Subword bi-gram for partial semantic overlap
            if len(word) > 3:
                bg = word[:3]
                h_bg = int(hashlib.md5(bg.encode("utf-8")).hexdigest(), 16)
                idx_bg = h_bg % self.dim
                vec[idx_bg] += 0.5 * sign

        # Compute L2 norm
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def get_embedding(self, text: str) -> List[float]:
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {"input": text, "model": self.model}
            with httpx.Client(timeout=10.0) as client:
                res = client.post("https://api.openai.com/v1/embeddings", json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            logger.warning(f"OpenAI embedding call failed ({e}), falling back to deterministic mock embedding")
            return MockEmbeddingProvider(dim=settings.EMBEDDING_DIM).get_embedding(text)


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def get_embedding(self, text: str) -> List[float]:
        try:
            import httpx
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent?key={self.api_key}"
            payload = {
                "model": f"models/{self.model}",
                "content": {"parts": [{"text": text}]}
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["embedding"]["values"]
        except Exception as e:
            logger.warning(f"Gemini embedding call failed ({e}), falling back to deterministic mock embedding")
            return MockEmbeddingProvider(dim=settings.EMBEDDING_DIM).get_embedding(text)


def get_embedding_provider() -> EmbeddingProvider:
    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "openai" and settings.EMBEDDING_API_KEY:
        return OpenAIEmbeddingProvider(settings.EMBEDDING_API_KEY, settings.EMBEDDING_MODEL or "text-embedding-3-small")
    elif provider == "gemini" and settings.EMBEDDING_API_KEY:
        return GeminiEmbeddingProvider(settings.EMBEDDING_API_KEY, settings.EMBEDDING_MODEL or "text-embedding-004")
    else:
        return MockEmbeddingProvider(dim=settings.EMBEDDING_DIM)

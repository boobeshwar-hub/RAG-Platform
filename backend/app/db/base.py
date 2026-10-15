import json
from sqlalchemy.types import TypeDecorator, Text
from app.db.session import Base
from app.core.config import settings

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


class VectorType(TypeDecorator):
    """
    Cross-database vector type.
    Maps to pgvector.sqlalchemy.Vector on PostgreSQL with pgvector,
    and falls back to JSON-serialized Text on SQLite.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            return dialect.type_descriptor(Vector(settings.EMBEDDING_DIM))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            return value
        if isinstance(value, str):
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, (bytes, bytearray)):
            try:
                import numpy as np
                return np.frombuffer(value, dtype=np.float32).tolist()
            except Exception:
                pass
        try:
            return json.loads(value)
        except Exception:
            return []

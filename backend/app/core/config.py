import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load .env file from project root or backend dir
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class Settings:
    PROJECT_NAME: str = "TruthGraph AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./truthgraph_dev.db"
    )

    # Security & JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-truthgraph-ai-hackathon-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # AI / LLM Providers
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock").lower()
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "mock-model")

    # Embedding Providers
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "mock").lower()
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "mock-embed-v1")
    EMBEDDING_DIM: int = 384  # Standard vector dimension for hybrid semantic search

    # Uploads & Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt", ".csv", ".xlsx"}

    # CORS
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def is_postgres(self) -> bool:
        return self.DATABASE_URL.startswith("postgresql")

    @property
    def cors_origins(self) -> List[str]:
        origins = [self.FRONTEND_ORIGIN, "http://localhost:3000", "http://127.0.0.1:5173", "http://localhost:5173"]
        return list(set(origins))


settings = Settings()

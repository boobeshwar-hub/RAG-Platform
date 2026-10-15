from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.db.session import engine, Base
import app.models  # Ensure all models are registered with Base
from app.api.routes import auth, documents, chat, conflicts, evidence, dashboard, system

# Setup structured logging
setup_logging()

# Auto-create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TruthGraph AI: Advanced Evidence-Grounded RAG Platform with Claim Verification and Conflict Resolution",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register System Routes at root and API v1
app.include_router(system.router)
app.include_router(system.router, prefix=settings.API_V1_STR)

# Register API v1 Routes
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(conflicts.router, prefix=settings.API_V1_STR)
app.include_router(evidence.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "tagline": "From scattered information to verified answers.",
        "api_docs": f"{settings.API_V1_STR}/docs",
        "health": "/health",
        "ready": "/ready"
    }

logger.info(f"Initialized {settings.PROJECT_NAME} v{settings.VERSION} on {settings.DATABASE_URL}")

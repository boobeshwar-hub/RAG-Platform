import os
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.core.config import settings

router = APIRouter(tags=["System"])

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@router.get("/ready")
def readiness_check(response: Response, db: Session = Depends(get_db)):
    checks = {
        "database": False,
        "upload_storage": False,
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "is_mock_ai": (settings.LLM_PROVIDER == "mock")
    }

    # 1. Database check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        checks["database_error"] = str(e)

    # 2. Upload storage check
    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        test_file = os.path.join(settings.UPLOAD_DIR, ".ready_probe")
        with open(test_file, "w") as f:
            f.write("probe")
        os.remove(test_file)
        checks["upload_storage"] = True
    except Exception as e:
        checks["storage_error"] = str(e)

    all_ready = checks["database"] and checks["upload_storage"]
    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "checks": checks}

    return {"status": "ready", "checks": checks}

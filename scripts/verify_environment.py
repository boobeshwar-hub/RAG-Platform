import sys
import os
from pathlib import Path

# Set up path to backend
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def verify():
    print("=" * 60)
    print(" TruthGraph AI - Environment & Dependency Verification")
    print("=" * 60)
    print(f"Python Version: {sys.version.split()[0]}")

    errors = []

    # 1. Config check
    try:
        from app.core.config import settings
        print(f"[OK] Configuration loaded. DB: {settings.DATABASE_URL}")
        print(f"[OK] Embedding Provider: {settings.EMBEDDING_PROVIDER} (dim={settings.EMBEDDING_DIM})")
        print(f"[OK] LLM Provider: {settings.LLM_PROVIDER}")
    except Exception as e:
        errors.append(f"Config Error: {e}")

    # 2. Database connectivity
    try:
        from app.db.session import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Database connection established.")
    except Exception as e:
        errors.append(f"Database Error: {e}")

    # 3. Document parsers
    for pkg, name in [("pypdf", "PDF"), ("docx", "DOCX"), ("openpyxl", "XLSX"), ("csv", "CSV")]:
        try:
            __import__(pkg)
            print(f"[OK] Document Extractor: {name} ({pkg}) installed.")
        except Exception as e:
            errors.append(f"Extractor Missing ({name}): {e}")

    # 4. Mock & Embedding test
    try:
        from app.services.embedding_service import get_embedding_provider
        prov = get_embedding_provider()
        emb = prov.get_embedding("Test authentication policy enforcement")
        assert len(emb) == settings.EMBEDDING_DIM, f"Vector dim {len(emb)} != {settings.EMBEDDING_DIM}"
        print(f"[OK] Embedding provider generates valid {len(emb)}-dimensional vectors.")
    except Exception as e:
        errors.append(f"Embedding Provider Error: {e}")

    # Summary
    print("-" * 60)
    if errors:
        print("VERIFICATION FAILED WITH ISSUES:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("ALL CRITICAL ENVIRONMENT CHECKS PASSED.")
        print("System is fully ready to run.")
        print("=" * 60)

if __name__ == "__main__":
    verify()

# TruthGraph AI

> **Tagline:** *From scattered information to verified answers.*

[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-12%2F12%20Passing-emerald)](file:///backend/tests)
[![Frontend Tests](https://img.shields.io/badge/Frontend%20Tests-5%2F5%20Passing-emerald)](file:///frontend/src/tests)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11%2B-blue)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript%20%7C%20Vite-cyan)](https://react.dev)
[![pgvector](https://img.shields.io/badge/Vector%20Search-PostgreSQL%20%2B%20pgvector-teal)](https://github.com/pgvector/pgvector)

---

## 1. Overview & Problem Statement

Organizations store critical business knowledge across scattered PDFs, DOCX policies, CSV server inventories, Excel spreadsheets, and plain text notes. Information is frequently outdated, contradictory, or incomplete. Standard RAG applications fail when faced with conflicting sources, often hallucinating a false synthesis or stating inaccurate facts without verification.

**TruthGraph AI** is an advanced Retrieval-Augmented Generation (RAG) platform that:
1. Ingests heterogeneous multi-format documents (PDF, DOCX, TXT, CSV, XLSX) while preserving precise page, row, and sheet locations.
2. Performs **hybrid retrieval** fusing lexical keyword search with semantic pgvector embeddings via **Reciprocal Rank Fusion (RRF)**.
3. Detects **factual contradictions**, **outdated policies**, and **qualifying exception clauses** across sources.
4. Generates evidence-grounded answers citing exact passage excerpts.
5. Enforces **claim-level verification**: extracts every factual claim, checks it against authentic retrieved passages, and **abstains** when evidence is missing or contradicted.
6. Guarantees **tenant isolation**, preventing cross-user data leakage.

---

## 2. Features & Current Limitations

### Implemented Features
- **Multi-Format Extraction Pipeline**: Robust extraction for PDF (page-aware), DOCX (paragraphs and tables), TXT (sections), CSV (row-by-row context with headers), and XLSX (sheet and row context).
- **Hybrid Search with RRF**: PostgreSQL full-text search + pgvector semantic vector search merged via Reciprocal Rank Fusion.
- **Conflict Detection Engine**: Detects factual contradictions, superseded audits, and approved policy exceptions with side-by-side excerpt comparisons.
- **Claim-by-Claim Verification**: Evaluates claims into `supported`, `partially_supported`, `contradicted`, or `insufficient_evidence`.
- **Honest Abstention**: Flags questions with missing evidence and qualifies uncertainty rather than hallucinating answers.
- **Traceable Citations**: Every citation links directly to a stored document chunk with verbatim excerpt and location.
- **Interactive UI**: Dark navy/white interface with Dashboard, Document Hub, AI Research Chat, Conflict Center, Evidence Explorer, and Evaluation telemetry.
- **Deterministic Mock Mode**: Full offline, zero-dependency mode out of the box requiring zero external paid API keys.
- **Plug-and-Play AI Providers**: Configurable support for live OpenAI and Google Gemini models via `.env`.

### Current Limitations
- **Scanned Image PDFs**: Does not perform OCR on scanned PDFs lacking text layers; reports "No readable content extracted" instead of guessing.
- **Vector Index Tuning**: Default vector dimension is 384; production deployments exceeding 1,000,000 chunks should enable HNSW indexing on pgvector.

---

## 3. Architecture Diagram

```mermaid
flowchart TD
    subgraph Client ["Frontend (React 18 + Vite + Tailwind CSS)"]
        UI["User Interface\n- Dashboard\n- Document Hub\n- AI Research Chat\n- Conflict Center\n- Evidence Explorer\n- Evaluation"]
        ClientAPI["Centralized API Client\n(Bearer JWT Auth)"]
        UI --> ClientAPI
    end

    subgraph Server ["Backend (FastAPI + Python 3.11+)"]
        Auth["Tenant Security & Auth Middleware"]
        Ingestion["Multi-Format Parser (PDF, DOCX, TXT, CSV, XLSX)"]
        Chunking["Location-Aware Overlapping Chunker"]
        Embedding["Embedding Engine (384-dim Vector)"]
        Hybrid["Hybrid Search (FTS + Vector + RRF)"]
        Conflicts["Conflict Detection Engine"]
        AnswerEng["Answer Synthesis Engine"]
        Verification["Claim-Level Verification & Abstention Engine"]
        Audit["Sanitized Audit Logger"]

        ClientAPI --> Auth
        Auth --> Ingestion
        Ingestion --> Chunking --> Embedding
        Auth --> Hybrid
        Hybrid --> Conflicts
        Hybrid --> AnswerEng
        AnswerEng --> Verification
        Verification --> Audit
    end

    subgraph Storage ["Persistence Layer"]
        DB[("PostgreSQL 16 + pgvector\n(SQLite Fallback Support)")]
        Disk[("Persistent Storage (uploads/)")]

        Chunking --> DB
        Embedding --> DB
        Conflicts --> DB
        Ingestion --> Disk
    end
```

---

## 4. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React, Vitest.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PyMuPDF/pypdf, python-docx, openpyxl, bcrypt, PyJWT, pytest, HTTPX.
- **Database & Search**: PostgreSQL 16, pgvector, PostgreSQL full-text search, Reciprocal Rank Fusion (with SQLite fallback for zero-dependency local runs).
- **Deployment**: Docker, Docker Compose, Nginx.

---

## 5. Prerequisites

- **Node.js**: v18.0.0 or later (v20+ recommended)
- **Python**: 3.11, 3.12, 3.13, or 3.14
- **Docker & Docker Compose** (Optional: for containerized deployment)

---

## 6. Windows PowerShell Setup Commands

### Step 1: Clone or Navigate to Project
```powershell
cd C:\Users\boobe\.gemini\antigravity\scratch\truthgraph-ai
```

### Step 2: Configure Environment
```powershell
Copy-Item .env.example .env
```

### Step 3: Run Environment Verification
```powershell
$env:PYTHONPATH=".\backend"
python .\scripts\verify_environment.py
```

### Step 4: Seed Synthetic Demo Data
```powershell
$env:PYTHONPATH=".\backend"
python .\scripts\seed_demo_data.py
```

### Step 5: Start Backend
```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Start Frontend (in a new terminal)
```powershell
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 7. Linux & macOS Setup Commands

```bash
# Clone and navigate
cd truthgraph-ai

# Copy environment file
cp .env.example .env

# Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Verify environment and seed demo data
export PYTHONPATH="./backend"
python3 scripts/verify_environment.py
python3 scripts/seed_demo_data.py

# Start Backend
cd backend && uvicorn app.main:app --reload --port 8000 &

# Start Frontend
cd ../frontend && npm install && npm run dev
```

---

## 8. Environment Variables & AI Provider Setup

All configurable variables are defined in `.env.example`:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/truthgraph_ai` | PostgreSQL connection string or `sqlite:///./truthgraph_dev.db` |
| `JWT_SECRET_KEY` | `dev-secret-key-truthgraph-ai-hackathon-2026` | 32+ byte secret for signing JWT access tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT expiration duration in minutes (24 hours) |
| `LLM_PROVIDER` | `mock` | AI Provider: `mock` (offline deterministic), `openai`, or `gemini` |
| `LLM_API_KEY` | *(empty)* | API Key for external LLM provider |
| `LLM_MODEL` | `mock-model` | Target model name (e.g. `gpt-4o-mini`, `gemini-1.5-flash`) |
| `EMBEDDING_PROVIDER` | `mock` | Embedding provider: `mock`, `openai`, or `gemini` |
| `EMBEDDING_API_KEY` | *(empty)* | API Key for external embedding provider |
| `EMBEDDING_MODEL` | `mock-embed-v1` | Embedding model (e.g. `text-embedding-3-small`) |
| `UPLOAD_DIR` | `./uploads` | Persistent directory for uploaded documents |
| `MAX_UPLOAD_SIZE_MB` | `25` | Maximum upload size per file in megabytes |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Allowed CORS origin for frontend |

### Using Live Google Gemini or OpenAI
To enable live AI generation instead of deterministic mock mode:
```env
LLM_PROVIDER=gemini
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-1.5-flash

EMBEDDING_PROVIDER=gemini
EMBEDDING_API_KEY=your_gemini_api_key_here
EMBEDDING_MODEL=text-embedding-004
```

---

## 9. Docker Compose Startup & Shutdown

### Build and Launch Full Stack
```bash
docker-compose up --build -d
```
This automatically starts:
- PostgreSQL 16 with pgvector extension on port `5432`.
- TruthGraph FastAPI backend on port `8000`.
- React frontend with Nginx on port `5173`.

### View Logs
```bash
docker-compose logs -f backend
```

### Stop Containers
```bash
docker-compose down
```

### Reset Database Volume
```bash
docker-compose down -v
```

---

## 10. Database Migrations

Alembic handles database migrations:

```powershell
cd backend
# Upgrade to latest schema
alembic upgrade head

# Generate a new migration revision
alembic revision -m "add_new_feature"
```

---

## 11. Synthetic Demo Scenario

The application includes a repeatable synthetic demo dataset for a fictional enterprise:
1. `security_policy.pdf`: Production servers must enforce Multi-Factor Authentication (MFA).
2. `server_inventory.csv`: Operational records showing 3 servers (`srv-prod-01`, `srv-prod-02`, `srv-prod-03`) with MFA disabled.
3. `exception_register.csv`: Approved exception `EXC-2026-088` valid until November 30, 2026 for `srv-prod-01`.
4. `previous_audit.txt`: Historical Q4 audit claiming 100% compliance across all servers.
5. `incident_response_guide.docx`: Severity-2 escalation procedures for unapproved disabled MFA.
6. `q3_datacenter_metrics.xlsx`: Host counts and scan timestamps.

### Benchmark Demo Query:
> *"Are all production servers compliant with the MFA policy? Identify non-compliant servers, valid exceptions, and any information that needs further verification."*

### Verified Pipeline Outcome:
- Retrieves evidence from policy, inventory, exception register, and audit.
- Cites exact supporting excerpts with locations (`Page 1`, `Row 4`, `Row 2`, `Section 2`).
- Identifies contradiction: historical audit claimed 100% compliance, but operational records refute this.
- Clarifies nuance: `srv-prod-01` has an approved exception, while `srv-prod-02` and `srv-prod-03` represent active violations.
- Abstains from declaring false full compliance and highlights needed follow-up verification.

---

## 12. Application URLs & Documentation

- **Web Frontend Application**: [http://localhost:5173](http://localhost:5173)
- **Interactive Swagger API Docs**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **ReDoc Technical Schema**: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)
- **Service Liveness Probe**: [http://localhost:8000/health](http://localhost:8000/health)
- **Service Readiness Probe**: [http://localhost:8000/ready](http://localhost:8000/ready)

### Pre-configured Demo Credentials:
- **Email**: `admin@truthgraph.ai`
- **Password**: `AdminPassword123!`

---

## 13. Test Commands & Verification

### Run Backend Tests (12 test cases)
```powershell
$env:PYTHONPATH=".\backend"
python -m pytest backend\tests -v
```

### Run Frontend Tests (5 test cases)
```powershell
cd frontend
npx vitest run
```

### Verify Frontend Production Build
```powershell
cd frontend
npm run build
```

---

## 14. Troubleshooting

- **Port 8000 or 5173 already in use**:
  Change port via `--port 8001` for uvicorn, or set `server.port` in `frontend/vite.config.ts`.
- **Database Connection Error**:
  If PostgreSQL is not running locally, TruthGraph AI automatically falls back to zero-dependency local SQLite (`sqlite:///./truthgraph_dev.db`).
- **File Upload Issues**:
  Ensure the uploaded file has a valid extension (`.pdf`, `.docx`, `.txt`, `.csv`, `.xlsx`) and does not exceed the configured `MAX_UPLOAD_SIZE_MB` (default 25MB).

---

## 15. Security Considerations

- **No Plaintext Passwords**: Uses salted bcrypt password hashes.
- **Tenant Isolation**: Every database query filters by `owner_id == current_user.id`.
- **Sanitized Logging**: Audit events scrub passwords, authorization tokens, and confidential document bodies before logging.
- **Untrusted Input Treatment**: Document contents are treated strictly as evidence data, not executable instructions.

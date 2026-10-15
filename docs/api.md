# TruthGraph AI — REST API Documentation

All API endpoints are versioned under `/api/v1` and generate interactive OpenAPI schemas at `/api/v1/docs` and `/api/v1/redoc`.

## Base URLs
- Local Development: `http://localhost:8000/api/v1`
- Docker Deployment: `http://localhost:8000/api/v1`

---

## 1. Authentication

### `POST /auth/register`
Creates a new tenant user account and issues a Bearer JWT access token.
- **Request Body:**
  ```json
  {
    "name": "Security Compliance Auditor",
    "email": "auditor@enterprise.com",
    "password": "Password123!"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": "uuid-v4",
      "name": "Security Compliance Auditor",
      "email": "auditor@enterprise.com",
      "role": "user",
      "is_active": true,
      "created_at": "2026-10-15T00:00:00Z"
    }
  }
  ```

### `POST /auth/login`
Authenticates existing credentials and returns a Bearer JWT access token.
- **Request Body:**
  ```json
  {
    "email": "admin@truthgraph.ai",
    "password": "AdminPassword123!"
  }
  ```
- **Response (200 OK):** `Token` schema.

### `GET /auth/me`
Returns the currently authenticated user profile.
- **Headers:** `Authorization: Bearer <TOKEN>`

---

## 2. Document Management

### `POST /documents/upload`
Uploads and indexes a multi-source enterprise document.
- **Multipart Form:** `file`: Binary file (PDF, DOCX, TXT, CSV, or XLSX). Maximum size: 25MB.
- **Response (201 Created):**
  ```json
  {
    "id": "doc-uuid",
    "owner_id": "user-uuid",
    "original_filename": "security_policy.pdf",
    "file_type": "pdf",
    "file_size": 18240,
    "checksum_sha256": "4a7f...",
    "processing_status": "completed",
    "chunks_count": 2,
    "upload_timestamp": "2026-10-15T00:00:00Z"
  }
  ```

### `GET /documents`
Lists all documents owned by the authenticated user.

### `GET /documents/{document_id}`
Retrieves document metadata and chunk statistics.

### `GET /documents/{document_id}/status`
Polls ingestion pipeline processing status (`pending`, `processing`, `completed`, `failed`).

### `DELETE /documents/{document_id}`
Permanently deletes the document and cascades deletion to all passage chunks, embeddings, claims, and conflicts. Returns `204 No Content`.

---

## 3. AI Research Chat & Verification

### `POST /chat/ask`
Submits a natural-language query to the hybrid RAG pipeline.
- **Request Body:**
  ```json
  {
    "question": "Are all production servers compliant with the MFA policy?",
    "conversation_id": "optional-uuid"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "message_id": "msg-uuid",
    "conversation_id": "conv-uuid",
    "role": "assistant",
    "content": "Based on the enterprise security documentation...",
    "verification_status": "partially_supported",
    "citations": [
      {
        "citation_id": "cit-1",
        "document_id": "doc-uuid",
        "document_filename": "security_policy.pdf",
        "chunk_id": "chunk-uuid",
        "location": "Page 1",
        "excerpt": "All production Linux and Windows servers must enforce Multi-Factor Authentication...",
        "score": 3.2
      }
    ],
    "claims_verification": [
      {
        "claim_text": "The corporate security policy explicitly requires MFA on all production servers",
        "status": "supported",
        "supporting_evidence_ids": ["chunk-uuid"],
        "contradicting_evidence_ids": [],
        "explanation": "Grounded directly in cited passage evidence (100% term alignment)."
      }
    ],
    "conflicts_detected": [
      {
        "id": "conflict-uuid",
        "subject": "MFA Compliance Status Discrepancy",
        "relationship_type": "contradicts",
        "conflict_category": "outdated_policy",
        "source_a_name": "previous_audit.txt",
        "source_a_location": "Section 2",
        "source_a_excerpt": "Finding: 100% of production servers were verified to be compliant...",
        "source_b_name": "server_inventory.csv",
        "source_b_location": "Row 4",
        "source_b_excerpt": "Server_Hostname: srv-prod-03; MFA_Status: Disabled...",
        "explanation": "Prior audit reported 100% compliance, but current operational inventory records identify MFA disabled on active servers."
      }
    ],
    "uncertainty_notes": "Historical audit statements contradict current inventory status; current operational data was treated as authoritative."
  }
  ```

### `GET /conversations`
Lists previous research conversation sessions.

### `GET /conversations/{conversation_id}/messages`
Retrieves the complete message history with citations and claim verifications for a session.

---

## 4. Conflict Center

### `GET /conflicts`
Retrieves detected contradictions and exceptions with optional status filtering (`?status=unresolved`).

### `PATCH /conflicts/{conflict_id}/review`
Updates the review status of a detected conflict (`unresolved`, `reviewed`, `resolved`).

---

## 5. Evidence & Provenance

### `GET /evidence/{evidence_id}`
Fetches verbatim passage text and provenance metadata for an exact chunk, enforcing user tenant ownership.

---

## 6. Dashboard & Evaluation

### `GET /dashboard/summary`
Returns database-backed metrics for total documents, completed, failed, questions asked, and recent audit activity.

### `GET /evaluation/summary`
Returns dynamically calculated precision, recall, citation integrity, and faithfulness metrics.

### `POST /evaluation/run`
Executes an automated benchmark evaluation suite across the user repository.

---

## 7. System Health

### `GET /health`
Basic service liveness probe.

### `GET /ready`
Readiness check verifying database connectivity and persistent upload storage availability. Returns HTTP 200 when ready, HTTP 503 otherwise.

import os
import sys
import csv
from datetime import datetime, timezone
from pathlib import Path

# Set up path to import app modules
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal, Base, engine
from app.models.user import User
from app.models.document import Document
from app.services.document_service import DocumentService
from fastapi import UploadFile

DEMO_USER_EMAIL = "admin@truthgraph.ai"
DEMO_USER_PASSWORD = "AdminPassword123!"
DEMO_USER_NAME = "Compliance Officer Admin"

def create_synthetic_files(temp_dir: str):
    os.makedirs(temp_dir, exist_ok=True)
    created_paths = {}

    # 1. security_policy.pdf
    pdf_path = os.path.join(temp_dir, "security_policy.pdf")
    # Write a valid standard single-page PDF containing the policy
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length 420 >> stream\n"
        b"BT\n/F1 12 Tf\n72 710 Td\n(APEX GLOBAL ENTERPRISE SECURITY DIRECTIVE - POL-SEC-2026-04) Tj\n"
        b"0 -24 Td\n(Section 4.1: Production Access Authentication Standards) Tj\n"
        b"0 -18 Td\n(All production Linux and Windows servers must enforce Multi-Factor Authentication (MFA).) Tj\n"
        b"0 -18 Td\n(Direct password-only SSH or RDP access is strictly prohibited across all production clusters.) Tj\n"
        b"0 -18 Td\n(Effective Date: January 15, 2026. Review Authority: Chief Information Security Officer.) Tj\n"
        b"0 -18 Td\n(Temporary exemptions must be approved by Security Governance and logged in the Exception Register.) Tj\n"
        b"ET\nendstream\nendobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000244 00000 n \n0000000717 00000 n \n"
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n786\n%%EOF\n"
    )
    with open(pdf_path, "wb") as f:
        f.write(pdf_content)
    created_paths["pdf"] = pdf_path

    # 2. server_inventory.csv
    csv_path = os.path.join(temp_dir, "server_inventory.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Server_Hostname", "Environment", "IP_Address", "OS", "MFA_Status", "Primary_Workload"])
        writer.writerow(["srv-prod-01", "Production", "10.0.1.14", "Ubuntu 24.04", "Disabled", "Core Database Primary"])
        writer.writerow(["srv-prod-02", "Production", "10.0.1.15", "RHEL 9.2", "Disabled", "Payment Gateway API"])
        writer.writerow(["srv-prod-03", "Production", "10.0.1.16", "Windows Server 2022", "Disabled", "Active Directory Replica"])
        writer.writerow(["srv-prod-04", "Production", "10.0.1.17", "Ubuntu 24.04", "Enabled", "Frontend Web Cluster 01"])
        writer.writerow(["srv-prod-05", "Production", "10.0.1.18", "Ubuntu 24.04", "Enabled", "Frontend Web Cluster 02"])
        writer.writerow(["srv-stage-01", "Staging", "10.0.2.10", "Ubuntu 24.04", "Disabled", "Staging Build Node"])
    created_paths["csv"] = csv_path

    # 3. exception_register.csv
    exc_path = os.path.join(temp_dir, "exception_register.csv")
    with open(exc_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Exception_ID", "Target_Asset", "Policy_Ref", "Justification", "Approval_Status", "Valid_From", "Valid_Until", "Approved_By"])
        writer.writerow([
            "EXC-2026-088",
            "srv-prod-01",
            "POL-SEC-2026-04",
            "Database clustering latency bug with PAM Duo module; patch scheduled for Q4 maintenance.",
            "Approved",
            "2026-02-01",
            "2026-11-30",
            "CISO Office"
        ])
    created_paths["exception_csv"] = exc_path

    # 4. previous_audit.txt
    txt_path = os.path.join(temp_dir, "previous_audit.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(
            "ANNUAL CYBERSECURITY COMPLIANCE AUDIT REPORT\n"
            "Audit Reference: AUD-2025-Q4-SUMMARY\n"
            "Audit Date: December 20, 2025\n"
            "Scope: Apex Global Production Infrastructure\n\n"
            "Executive Finding:\n"
            "During the Q4 2025 assessment, all enterprise production servers were evaluated for identity verification.\n"
            "Finding: 100% of production servers were verified to be compliant with access security controls.\n"
            "All tested endpoints exhibited active Multi-Factor Authentication (MFA) enforcement with zero open discrepancies.\n"
            "Sign-off: Lead Auditor J. Vance, CISSP.\n"
        )
    created_paths["txt"] = txt_path

    # 5. q3_datacenter_metrics.xlsx (openpyxl)
    xlsx_path = os.path.join(temp_dir, "q3_datacenter_metrics.xlsx")
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Infrastructure_Health"
        ws.append(["Cluster_Zone", "Total_Hosts", "MFA_Enforced_Count", "Patch_Compliance_Pct", "Last_Scanned"])
        ws.append(["US-East-Prod", 150, 147, 98.0, "2026-10-10"])
        ws.append(["EU-West-Prod", 90, 90, 100.0, "2026-10-12"])
        wb.save(xlsx_path)
        created_paths["xlsx"] = xlsx_path
    except Exception as e:
        print(f"XLSX generation note: {e}")

    # 6. incident_response_guide.docx (python-docx)
    docx_path = os.path.join(temp_dir, "incident_response_guide.docx")
    try:
        import docx
        doc = docx.Document()
        doc.add_heading("Production Security Incident Escalation Guide", level=1)
        doc.add_paragraph("Section 1: Unauthorized Access and Authentication Bypass.")
        doc.add_paragraph("Any production asset detected operating with disabled MFA without an active ticket in the Exception Register must be reported within 2 hours as a Severity-2 Security Incident.")
        doc.save(docx_path)
        created_paths["docx"] = docx_path
    except Exception as e:
        print(f"DOCX generation note: {e}")

    return created_paths


def seed_database():
    print("Initializing Database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Create Demo User
        user = db.query(User).filter(User.email == DEMO_USER_EMAIL).first()
        if not user:
            print(f"Creating demo user: {DEMO_USER_EMAIL}...")
            user = User(
                name=DEMO_USER_NAME,
                email=DEMO_USER_EMAIL,
                password_hash=get_password_hash(DEMO_USER_PASSWORD),
                role="admin",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print("Demo user created.")
        else:
            print(f"Demo user {DEMO_USER_EMAIL} already exists.")

        # Create Synthetic Files
        temp_dir = os.path.join(settings.UPLOAD_DIR, "synthetic_seed_sources")
        file_map = create_synthetic_files(temp_dir)

        print(f"Ingesting {len(file_map)} synthetic demo files into pipeline...")
        for key, filepath in file_map.items():
            filename = os.path.basename(filepath)
            checksum = DocumentService.calculate_checksum(filepath)

            existing = db.query(Document).filter(
                Document.owner_id == user.id,
                Document.checksum_sha256 == checksum
            ).first()

            if existing:
                print(f"Document '{filename}' already ingested ({existing.processing_status}). Skipping duplicate.")
                continue

            with open(filepath, "rb") as f:
                upload_file = UploadFile(
                    filename=filename,
                    file=f
                )
                doc = DocumentService.save_and_create_document(db, upload_file, user.id)
                print(f"Ingested '{filename}' -> Status: {doc.processing_status}")

        print("\n=== Demo Seed Completed Successfully ===")
        print(f"Demo User Credentials:")
        print(f"Email:    {DEMO_USER_EMAIL}")
        print(f"Password: {DEMO_USER_PASSWORD}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

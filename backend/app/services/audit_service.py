import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.core.logging import logger

def log_audit_event(
    db: Session,
    action: str,
    target_type: str,
    actor_id: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """
    Persists a security-relevant audit event.
    Sanitizes details to ensure no credentials, tokens, or raw confidential texts are logged.
    """
    safe_details = details or {}
    # Mask any potential sensitive keys
    sensitive_keys = {"password", "token", "access_token", "secret", "authorization"}
    clean_details = {
        k: ("***REDACTED***" if k.lower() in sensitive_keys else v)
        for k, v in safe_details.items()
    }

    audit_entry = AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details_json=json.dumps(clean_details),
        ip_address=ip_address
    )
    try:
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        logger.info(f"Audit event recorded: {action} on {target_type}:{target_id} by {actor_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to record audit event: {e}")
    return audit_entry

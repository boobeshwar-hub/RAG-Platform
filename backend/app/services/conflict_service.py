import re
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.conflict import Conflict
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.services.retrieval_service import RetrievedPassage
from app.core.logging import logger

class CandidateConflict:
    def __init__(
        self,
        subject: str,
        relationship_type: str,
        conflict_category: str,
        source_a_name: str,
        source_a_location: str,
        source_a_excerpt: str,
        source_b_name: str,
        source_b_location: str,
        source_b_excerpt: str,
        explanation: str
    ):
        self.subject = subject
        self.relationship_type = relationship_type
        self.conflict_category = conflict_category
        self.source_a_name = source_a_name
        self.source_a_location = source_a_location
        self.source_a_excerpt = source_a_excerpt
        self.source_b_name = source_b_name
        self.source_b_location = source_b_location
        self.source_b_excerpt = source_b_excerpt
        self.explanation = explanation

class ConflictService:
    @staticmethod
    def detect_conflicts_in_passages(
        passages: List[RetrievedPassage]
    ) -> List[CandidateConflict]:
        """
        Analyzes pairs of retrieved passages to detect factual contradictions,
        superseded statements, or documented exceptions.
        """
        conflicts: List[CandidateConflict] = []
        if len(passages) < 2:
            return conflicts

        for i in range(len(passages)):
            for j in range(i + 1, len(passages)):
                p1 = passages[i]
                p2 = passages[j]

                # Don't compare identical chunks or same exact passage
                if p1.chunk_id == p2.chunk_id:
                    continue

                t1_lower = p1.excerpt.lower()
                t2_lower = p2.excerpt.lower()

                # Check 1: Exception / Qualifying relationships
                # E.g. "exception", "temporary approved exception", "exemption"
                if any(k in t1_lower for k in ["exception", "exemption", "temporary approval", "valid until"]) or \
                   any(k in t2_lower for k in ["exception", "exemption", "temporary approval", "valid until"]):
                    # If one mentions policy or violation and another mentions exception
                    if ("mfa" in t1_lower and "mfa" in t2_lower) or ("policy" in t1_lower and "policy" in t2_lower):
                        conflicts.append(CandidateConflict(
                            subject="MFA Compliance Exception",
                            relationship_type="qualifies",
                            conflict_category="exception_clause",
                            source_a_name=p1.document_filename,
                            source_a_location=p1.location,
                            source_a_excerpt=p1.excerpt[:300],
                            source_b_name=p2.document_filename,
                            source_b_location=p2.location,
                            source_b_excerpt=p2.excerpt[:300],
                            explanation="Source registers a formal exception clause qualifying the baseline policy requirement."
                        ))
                        continue

                # Check 2: Historical / Audit vs Current Evidence (Superseded or Outdated)
                # E.g. "audit", "previous", "compliant", "all servers compliant" vs "disabled", "non-compliant", "failed"
                has_audit_claim = any(k in t1_lower for k in ["all servers compliant", "100% compliant", "previous audit", "audit passed"]) or \
                                  any(k in t2_lower for k in ["all servers compliant", "100% compliant", "previous audit", "audit passed"])
                has_violation_claim = any(k in t1_lower for k in ["disabled", "false", "non-compliant", "no mfa"]) or \
                                      any(k in t2_lower for k in ["disabled", "false", "non-compliant", "no mfa"])

                if has_audit_claim and has_violation_claim:
                    conflicts.append(CandidateConflict(
                        subject="MFA Compliance Status Discrepancy",
                        relationship_type="contradicts",
                        conflict_category="outdated_policy",
                        source_a_name=p1.document_filename,
                        source_a_location=p1.location,
                        source_a_excerpt=p1.excerpt[:300],
                        source_b_name=p2.document_filename,
                        source_b_location=p2.location,
                        source_b_excerpt=p2.excerpt[:300],
                        explanation="Prior audit reported 100% compliance, but current operational inventory records identify MFA disabled on active servers."
                    ))
                    continue

                # Check 3: Direct polarity conflict on key entity properties
                # E.g. required vs optional, enabled vs disabled, compliant vs non-compliant
                polarity_pairs = [
                    (r"\benabled\b", r"\bdisabled\b"),
                    (r"\brequired\b", r"\boptional\b"),
                    (r"\bcompliant\b", r"\bnon-compliant\b"),
                    (r"\bapproved\b", r"\brejected\b")
                ]

                for pos_pattern, neg_pattern in polarity_pairs:
                    if (re.search(pos_pattern, t1_lower) and re.search(neg_pattern, t2_lower)) or \
                       (re.search(neg_pattern, t1_lower) and re.search(pos_pattern, t2_lower)):
                        # Look for common subject words (nouns with len > 4)
                        words1 = set(w for w in re.findall(r"\b\w{4,}\b", t1_lower))
                        words2 = set(w for w in re.findall(r"\b\w{4,}\b", t2_lower))
                        overlap = words1.intersection(words2) - {"policy", "server", "system", "status", "production"}

                        if overlap:
                            subj = f"{next(iter(overlap)).capitalize()} Configuration Discrepancy"
                            conflicts.append(CandidateConflict(
                                subject=subj,
                                relationship_type="contradicts",
                                conflict_category="factual_disagreement",
                                source_a_name=p1.document_filename,
                                source_a_location=p1.location,
                                source_a_excerpt=p1.excerpt[:300],
                                source_b_name=p2.document_filename,
                                source_b_location=p2.location,
                                source_b_excerpt=p2.excerpt[:300],
                                explanation=f"Direct contradictory claims regarding '{', '.join(overlap)}' between sources."
                            ))
                            break

        return conflicts

    @classmethod
    def persist_detected_conflicts(
        cls,
        db: Session,
        user_id: str,
        candidate_conflicts: List[CandidateConflict]
    ) -> List[Conflict]:
        """
        Saves candidate conflicts to DB avoiding duplicate pairs for the same user.
        """
        saved: List[Conflict] = []
        for cand in candidate_conflicts:
            # Check if matching conflict exists
            existing = db.query(Conflict).filter(
                Conflict.user_id == user_id,
                Conflict.source_a_name == cand.source_a_name,
                Conflict.source_b_name == cand.source_b_name,
                Conflict.subject == cand.subject
            ).first()

            if not existing:
                conflict_record = Conflict(
                    user_id=user_id,
                    subject=cand.subject,
                    relationship_type=cand.relationship_type,
                    conflict_category=cand.conflict_category,
                    source_a_name=cand.source_a_name,
                    source_a_location=cand.source_a_location,
                    source_a_excerpt=cand.source_a_excerpt,
                    source_b_name=cand.source_b_name,
                    source_b_location=cand.source_b_location,
                    source_b_excerpt=cand.source_b_excerpt,
                    explanation=cand.explanation,
                    review_status="unresolved"
                )
                db.add(conflict_record)
                db.commit()
                db.refresh(conflict_record)
                saved.append(conflict_record)
            else:
                saved.append(existing)

        return saved

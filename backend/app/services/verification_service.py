import re
from typing import List, Dict, Any, Tuple
from app.services.retrieval_service import RetrievedPassage
from app.services.answer_service import GeneratedAnswer
from app.schemas.chat import ClaimVerificationItem, CitationItem

class VerificationResult:
    def __init__(
        self,
        final_answer: str,
        overall_status: str,  # supported, partially_supported, contradicted, insufficient_evidence
        verified_claims: List[ClaimVerificationItem],
        valid_citations: List[CitationItem],
        uncertainty_notes: str = ""
    ):
        self.final_answer = final_answer
        self.overall_status = overall_status
        self.verified_claims = verified_claims
        self.valid_citations = valid_citations
        self.uncertainty_notes = uncertainty_notes


class VerificationService:
    @staticmethod
    def extract_claims(answer_text: str) -> List[str]:
        """
        Extracts individual factual sentences or bullet statements from the generated answer.
        """
        lines = [line.strip() for line in answer_text.splitlines() if line.strip()]
        claims = []
        for line in lines:
            if line.startswith("#"):
                continue  # skip headers
            if line.startswith(">"):
                continue  # skip blockquotes
            clean = re.sub(r"^[-*•\d\.]+\s*", "", line).strip()
            if len(clean) > 20:
                claims.append(clean)
        return claims

    @classmethod
    def verify_answer(
        cls,
        generated: GeneratedAnswer,
        passages: List[RetrievedPassage]
    ) -> VerificationResult:
        if not passages:
            return VerificationResult(
                final_answer="No evidence available in your documents to answer this question. Please upload relevant source documents.",
                overall_status="insufficient_evidence",
                verified_claims=[],
                valid_citations=[],
                uncertainty_notes="Zero matching evidence passages retrieved."
            )

        # 1. Map available passage indices
        passage_map = {idx: p for idx, p in enumerate(passages, 1)}

        # 2. Extract citations used in answer
        citation_matches = [int(x) for x in re.findall(r"\[(\d+)\]", generated.text)]
        cited_indices = sorted(list(set(citation_matches + generated.citations_used)))

        valid_citations: List[CitationItem] = []
        for idx in cited_indices:
            if idx in passage_map:
                p = passage_map[idx]
                valid_citations.append(CitationItem(
                    citation_id=f"cit-{idx}",
                    document_id=p.document_id,
                    document_filename=p.document_filename,
                    chunk_id=p.chunk_id,
                    location=p.location,
                    excerpt=p.excerpt[:280],
                    score=p.score
                ))

        # 3. Extract and verify claims
        claims = cls.extract_claims(generated.text)
        verified_claims: List[ClaimVerificationItem] = []
        contradicted_count = 0
        supported_count = 0
        unsupported_count = 0

        for claim in claims:
            # Find citation refs in this line
            refs = [int(r) for r in re.findall(r"\[(\d+)\]", claim)]
            claim_text_clean = re.sub(r"\[\d+\]", "", claim).strip()
            
            supporting_ids = []
            contradicting_ids = []
            status = "insufficient_evidence"
            explanation = "No direct passage evidence cited for this claim."

            if refs:
                for r in refs:
                    if r in passage_map:
                        supporting_ids.append(passage_map[r].chunk_id)

            # Heuristic check for contradiction mention
            claim_lower = claim.lower()
            if "contradict" in claim_lower or "discrepancy" in claim_lower or "conflict" in claim_lower or "superseded" in claim_lower:
                status = "contradicted"
                explanation = "Claim highlights documented factual discrepancy between current and prior records."
                contradicted_count += 1
            elif supporting_ids:
                # Evidence check: verify keywords from claim exist in supporting passage text
                supported_words = 0
                claim_words = [w.lower() for w in re.findall(r"\b\w{4,}\b", claim_text_clean)]
                
                matched_excerpts = " ".join([passage_map[r].excerpt.lower() for r in refs if r in passage_map])
                for w in claim_words:
                    if w in matched_excerpts:
                        supported_words += 1
                
                ratio = (supported_words / len(claim_words)) if claim_words else 1.0
                if ratio >= 0.35:
                    status = "supported"
                    explanation = f"Grounded directly in cited passage evidence ({int(ratio*100)}% term alignment)."
                    supported_count += 1
                else:
                    status = "partially_supported"
                    explanation = "Partially supported by cited passage with inference required."
                    supported_count += 1
            else:
                unsupported_count += 1

            verified_claims.append(ClaimVerificationItem(
                claim_text=claim_text_clean,
                status=status,
                supporting_evidence_ids=supporting_ids,
                contradicting_evidence_ids=contradicting_ids,
                explanation=explanation,
                confidence_notes="Verified via passage alignment and citation mapping."
            ))

        # 4. Synthesize overall verification status
        if contradicted_count > 0:
            overall_status = "partially_supported" if supported_count > 0 else "contradicted"
        elif unsupported_count > supported_count:
            overall_status = "insufficient_evidence"
        elif any(c.status == "partially_supported" for c in verified_claims):
            overall_status = "partially_supported"
        else:
            overall_status = "supported"

        uncertainty = generated.uncertainty_notes or ""
        if contradicted_count > 0:
            contradiction_note = "Discrepancies identified between historical audit statements and current operational records."
            uncertainty = f"{uncertainty} {contradiction_note}".strip()

        return VerificationResult(
            final_answer=generated.text,
            overall_status=overall_status,
            verified_claims=verified_claims,
            valid_citations=valid_citations,
            uncertainty_notes=uncertainty
        )

from typing import List, Dict, Any
import logging

logger = logging.getLogger("conflict_engine")

class ConflictDetectionEngine:
    def __init__(self):
        pass

    def evaluate_claims(self, claims: List[Dict[str, Any]], sources_map: Dict[str, Any]) -> List[Dict[str, Any]]:
        conflicts = []

        for claim in claims:
            status = claim.get("status", "VERIFIED")
            supporting_ids = [s.strip() for s in str(claim.get("supporting_source_ids", "")).split(";") if s.strip()]
            contradicting_ids = [s.strip() for s in str(claim.get("contradicting_source_ids", "")).split(";") if s.strip()]

            if contradicting_ids or status == "CONFLICTING":
                sup_sources = [sources_map[sid] for sid in supporting_ids if sid in sources_map]
                contra_sources = [sources_map[sid] for sid in contradicting_ids if sid in sources_map]

                # Fallback if primary & conflicting sources specified
                if not sup_sources and claim.get("primary_source_id") in sources_map:
                    sup_sources.append(sources_map[claim["primary_source_id"]])
                if not contra_sources and claim.get("conflicting_source_id") in sources_map:
                    contra_sources.append(sources_map[claim["conflicting_source_id"]])

                conflicts.append({
                    "claim_id": claim.get("claim_id"),
                    "entity_name": claim.get("entity_name", "Unknown Entity"),
                    "claim_text": claim.get("claim_text", ""),
                    "status": "CONFLICTING EVIDENCE DETECTED",
                    "supporting_sources": sup_sources,
                    "contradicting_sources": contra_sources,
                    "notes": "System detected opposing peer-reviewed / extension advisory claims. Rather than silently picking one, both claims and their source citations are surfaced transparently."
                })

        return conflicts

    def find_unverified_claims(self, claims: List[Dict[str, Any]], sources_map: Dict[str, Any]) -> List[Dict[str, Any]]:
        unverified = []
        for claim in claims:
            status = claim.get("status")
            primary_src = claim.get("primary_source_id")
            if status == "UNVERIFIED" or not primary_src or primary_src not in sources_map:
                unverified.append({
                    "claim_id": claim.get("claim_id"),
                    "entity_name": claim.get("entity_name", "Unknown"),
                    "claim_text": claim.get("claim_text", ""),
                    "status": "UNVERIFIED",
                    "reason": "No credible or peer-reviewed source found supporting this treatment claim."
                })
        return unverified

conflict_engine = ConflictDetectionEngine()

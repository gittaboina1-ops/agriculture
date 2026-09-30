from typing import Dict, Any, List, Optional
import os
import pandas as pd
import json
import logging

logger = logging.getLogger("provenance_tracker")

class ProvenanceTracker:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.claims: List[Dict[str, Any]] = []
        self._load_sources()

    def _load_sources(self):
        sources_csv = os.path.join(self.data_dir, "sources.csv")
        if os.path.exists(sources_csv):
            df = pd.read_csv(sources_csv)
            for _, row in df.iterrows():
                sid = str(row["source_id"]).strip()
                self.sources[sid] = {
                    "source_id": sid,
                    "title": row.get("title", ""),
                    "source_type": row.get("source_type", ""),
                    "authors_or_publisher": row.get("authors_or_publisher", ""),
                    "publication_year": int(row.get("publication_year", 2024)),
                    "confidence_score": float(row.get("confidence_score", 0.9)),
                    "summary": row.get("summary", ""),
                    "is_synthetic": bool(row.get("is_synthetic", False))
                }

        claims_csv = os.path.join(self.data_dir, "claims.csv")
        if os.path.exists(claims_csv):
            df_c = pd.read_csv(claims_csv)
            for _, row in df_c.iterrows():
                self.claims.append({
                    "claim_id": str(row.get("claim_id")),
                    "entity_id": str(row.get("entity_id")),
                    "entity_name": str(row.get("entity_name")),
                    "claim_text": str(row.get("claim_text")),
                    "claim_type": str(row.get("claim_type")),
                    "status": str(row.get("status")),
                    "primary_source_id": str(row.get("primary_source_id")) if pd.notna(row.get("primary_source_id")) else None,
                    "conflicting_source_id": str(row.get("conflicting_source_id")) if pd.notna(row.get("conflicting_source_id")) else None,
                    "supporting_source_ids": str(row.get("supporting_source_ids")) if pd.notna(row.get("supporting_source_ids")) else "",
                    "contradicting_source_ids": str(row.get("contradicting_source_ids")) if pd.notna(row.get("contradicting_source_ids")) else "",
                    "confidence": float(row.get("confidence", 0.8)),
                    "is_synthetic": bool(row.get("is_synthetic", False))
                })

    def get_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        return self.sources.get(source_id)

    def get_all_sources(self) -> List[Dict[str, Any]]:
        return list(self.sources.values())

    def get_provenance_for_claim(self, claim_id: str) -> Dict[str, Any]:
        claim = next((c for c in self.claims if c["claim_id"] == claim_id), None)
        if not claim:
            return {"error": "Claim not found"}

        sup_ids = [s.strip() for s in str(claim.get("supporting_source_ids", "")).split(";") if s.strip()]
        contra_ids = [s.strip() for s in str(claim.get("contradicting_source_ids", "")).split(";") if s.strip()]

        return {
            "claim": claim,
            "supporting_sources": [self.sources[sid] for sid in sup_ids if sid in self.sources],
            "contradicting_sources": [self.sources[sid] for sid in contra_ids if sid in self.sources],
            "status": claim.get("status"),
            "provenance_chain": [
                {"step": "Primary Document Evidence", "sources": [self.sources.get(claim.get("primary_source_id"))] if claim.get("primary_source_id") in self.sources else []},
                {"step": "Field Validation / Observation", "source_type": "District Extension / Farmer Log"}
            ]
        }

    def get_provenance_coverage(self) -> Dict[str, Any]:
        total_claims = len(self.claims)
        sourced_claims = sum(1 for c in self.claims if c.get("primary_source_id") in self.sources)
        coverage_pct = round((sourced_claims / total_claims * 100), 2) if total_claims > 0 else 0.0
        return {
            "total_claims": total_claims,
            "sourced_claims": sourced_claims,
            "coverage_percentage": coverage_pct,
            "total_sources_cataloged": len(self.sources)
        }

provenance_tracker = ProvenanceTracker()

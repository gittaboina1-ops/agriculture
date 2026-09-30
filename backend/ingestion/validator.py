"""
Ontology Validation & Schema Enforcement Module.
Enforces strict relationship ontology and entity constraints on LLM/NLP outputs before graph insertion.
Rejects malformed or unsupported edges.
"""

from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger("ingestion_validator")

# Supported canonical ontology mappings: (Source Label, Relationship) -> Target Label
ALLOWED_RELATIONSHIPS = {
    ("Crop", "SUSCEPTIBLE_TO"): ["Disease"],
    ("Disease", "TREATED_BY"): ["Treatment"],
    ("Disease", "ASSOCIATED_WITH"): ["WeatherCondition"],
    ("Crop", "SUITABLE_FOR"): ["Soil"],
    ("Observation", "OBSERVED_ON"): ["Crop"],
    ("Observation", "INDICATES_DISEASE"): ["Disease"],
    ("Sensor", "REPORTS_CONDITION"): ["WeatherCondition"],
    ("Claim", "SUPPORTED_BY"): ["Source"],
    ("Claim", "CONTRADICTED_BY"): ["Source"]
}

class IngestionValidator:
    def __init__(self):
        pass

    def validate_relationship(
        self,
        subject_entity: Dict[str, Any],
        relation: str,
        object_entity: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validates whether a subject -> relation -> object triple is permitted under the graph ontology.
        """
        sub_label = subject_entity.get("label", "").capitalize()
        obj_label = object_entity.get("label", "").capitalize()
        rel = relation.strip().upper()

        key = (sub_label, rel)
        if key not in ALLOWED_RELATIONSHIPS:
            return False, f"Ontology mismatch: ({sub_label})-[:{rel}]->({obj_label}) is not in allowed relationship types."

        allowed_target_labels = ALLOWED_RELATIONSHIPS[key]
        if obj_label not in allowed_target_labels:
            return False, f"Invalid target entity type '{obj_label}' for ({sub_label})-[:{rel}]. Expected one of: {allowed_target_labels}."

        return True, "Valid relationship according to ontology schema."

    def validate_extraction_payload(self, raw_payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates raw JSON extracted from LLM or NLP.
        """
        if not isinstance(raw_payload, dict):
            return False, "Extraction output is not a JSON object.", {}

        entities = raw_payload.get("entities", [])
        relationships = raw_payload.get("relationships", [])
        claims = raw_payload.get("claims", [])

        if not isinstance(entities, list) or not isinstance(relationships, list) or not isinstance(claims, list):
            return False, "Entities, relationships, or claims missing or not formatted as lists.", {}

        # Filter valid entities
        valid_entities = []
        for e in entities:
            if isinstance(e, dict) and e.get("name") and e.get("type"):
                valid_entities.append(e)

        # Filter valid relationships
        valid_relationships = []
        for r in relationships:
            if isinstance(r, dict) and r.get("subject") and r.get("relation") and r.get("object"):
                valid_relationships.append(r)

        # Filter valid claims
        valid_claims = []
        for c in claims:
            if isinstance(c, dict) and c.get("statement") and c.get("polarity"):
                valid_claims.append(c)

        cleaned = {
            "entities": valid_entities,
            "relationships": valid_relationships,
            "claims": valid_claims
        }
        return True, "Extraction payload passed format validation.", cleaned

ingestion_validator = IngestionValidator()

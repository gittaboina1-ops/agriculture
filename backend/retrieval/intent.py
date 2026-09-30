import re
from typing import Dict, Any, List, Tuple

# Supported Canonical Intents
INTENT_CROP_DISEASE = "CROP_DISEASE"
INTENT_SOIL_SUITABILITY = "SOIL_SUITABILITY"
INTENT_DISEASE_RISK = "DISEASE_RISK"
INTENT_TREATMENT = "TREATMENT"
INTENT_WEATHER_RISK = "WEATHER_RISK"
INTENT_EVIDENCE_PROVENANCE = "EVIDENCE_PROVENANCE"
INTENT_CONFLICT = "CONFLICT"
INTENT_DATA_QUALITY = "DATA_QUALITY"
INTENT_GENERAL = "GENERAL_AGRICULTURAL_QUERY"

class IntentDetector:
    def __init__(self):
        pass

    def detect_intent(self, query: str) -> str:
        q = query.lower().strip()

        # 1. Data Quality / Sensor corruption checks
        if any(term in q for term in ["sensor", "invalid reading", "bad data", "corrupt", "telemetry error", "data quality", "readings rejected"]):
            return INTENT_DATA_QUALITY

        # 2. Conflicting Claims
        if any(term in q for term in ["conflict", "disagree", "contradict", "opposing", "disputed"]):
            return INTENT_CONFLICT

        # 3. Provenance / Source Evidence
        if any(term in q for term in ["where did this information come from", "evidence support", "what evidence", "cite", "provenance", "source of"]):
            # If specifically asking about treatment evidence, it could be provenance or treatment; priority to provenance
            return INTENT_EVIDENCE_PROVENANCE

        # 4. Soil Suitability & Land Requirements
        if any(term in q for term in ["soil", "drainage", "land condition", "ground", "ph of soil", "suitable soil"]):
            return INTENT_SOIL_SUITABILITY

        # 5. Disease Risk / Why is my crop at risk
        if ("why" in q and ("risk" in q or "disease" in q or "blight" in q)) or ("high risk" in q or "risk level" in q or "disease risk" in q):
            return INTENT_DISEASE_RISK

        # 6. Treatments / Fungicides / Management
        if any(term in q for term in ["treatment", "cure", "spray", "manage", "control", "fungicide", "bactericide", "remedy"]):
            return INTENT_TREATMENT

        # 7. Weather & Microclimate Risks
        if any(term in q for term in ["weather", "temperature", "humidity", "rainfall", "climate", "monsoon"]):
            return INTENT_WEATHER_RISK

        # 8. Diseases affecting a crop
        if any(term in q for term in ["disease", "pathogen", "infection", "blight", "wilt", "mildew", "rot", "affect", "attack"]):
            return INTENT_CROP_DISEASE

        return INTENT_GENERAL

intent_detector = IntentDetector()

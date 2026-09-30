import re
import numpy as np
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

# Exemplar anchors for semantic similarity comparison
INTENT_ANCHORS = {
    INTENT_SOIL_SUITABILITY: [
        "What soil conditions are suitable for tomato?",
        "What type of soil is best for growing tomatoes?",
        "Which soil is good for tomatoes?",
        "What kind of soil should I use for tomato cultivation?",
        "soil drainage and optimal pH requirements for vegetables"
    ],
    INTENT_DISEASE_RISK: [
        "Why is my tomato crop at high disease risk?",
        "Why is my crop vulnerable to disease and what factors cause it?",
        "What is increasing the infection risk in my field?",
        "Why is there a high threat of fungal blight on tomatoes?"
    ],
    INTENT_CROP_DISEASE: [
        "What diseases commonly affect tomato?",
        "Which pathogens and infections attack tomatoes?",
        "What plant diseases does tomato suffer from?",
        "common diseases in solanaceous crops"
    ],
    INTENT_TREATMENT: [
        "What treatments are associated with Early Blight?",
        "What sprays and fungicides control blight?",
        "How can I treat and cure tomato plant disease?",
        "recommended treatments and fungicides for early blight"
    ],
    INTENT_EVIDENCE_PROVENANCE: [
        "What evidence supports Neem Oil Extract?",
        "Where did this agricultural information come from?",
        "What citations and research papers back up this claim?",
        "evidence and sources behind this recommendation"
    ],
    INTENT_CONFLICT: [
        "Are there conflicting recommendations for Neem Oil Extract?",
        "Do sources and research disagree about Neem Oil?",
        "Is there contradictory evidence between advisories and trials?",
        "disputed claims and opposing recommendations"
    ],
    INTENT_WEATHER_RISK: [
        "What weather conditions increase Early Blight risk?",
        "How does temperature and humidity affect crop fungal infection?",
        "Does rain and high humidity increase disease development?",
        "environmental triggers and microclimate risks"
    ],
    INTENT_DATA_QUALITY: [
        "Are there any invalid sensor readings?",
        "Are any telemetry values corrupted or out of range?",
        "Did the system reject bad sensor data?",
        "data quality and anomalous telemetry reports"
    ]
}

class IntentDetector:
    def __init__(self):
        self.encoder = None
        self._anchor_embeddings = {}

    def attach_encoder(self, encoder):
        """Attaches a sentence-transformer encoder for semantic cosine matching."""
        self.encoder = encoder
        if self.encoder:
            try:
                for intent, examples in INTENT_ANCHORS.items():
                    emb = self.encoder.encode(examples, normalize_embeddings=True)
                    self._anchor_embeddings[intent] = emb
            except Exception:
                self.encoder = None

    def detect_intent(self, query: str) -> str:
        q = query.lower().strip()

        # 1. High-precision rule heuristics (English, Telugu, Hindi)
        if any(term in q for term in ["invalid reading", "bad sensor", "corrupt", "telemetry error", "data quality", "readings rejected", "invalid sensor", "సెన్సార్", "సరికాని", "తిరస్కరించిన", "सेंसर", "अमान्य", "खराब रीडिंग"]):
            return INTENT_DATA_QUALITY

        if any(term in q for term in ["conflict", "disagree", "contradict", "opposing", "disputed", "విరుద్ధ", "తేడాలు", "వివాదం", "विरोधी", "विवादित", "मतभेद"]):
            return INTENT_CONFLICT

        if any(term in q for term in ["where did this information come from", "evidence support", "evidence supports", "what evidence", "cite", "provenance", "source of", "ఆధారాలు", "సాక్ష్యం", "మూలం", "साक्ष्य", "प्रमाण", "स्रोत"]):
            return INTENT_EVIDENCE_PROVENANCE

        if any(term in q for term in ["soil", "drainage", "ground condition", "ph of soil", "suitable soil", "type of soil", "which soil", "kind of soil", "నేల", "మట్టి", "భూమి", "సాగుకు అనుకూలమైన నేల", "मिट्टी", "भूमि"]):
            return INTENT_SOIL_SUITABILITY

        if ("why" in q and ("risk" in q or "disease" in q or "blight" in q)) or any(term in q for term in ["high risk", "disease risk", "risk level", "ఎందుకు ప్రమాదం", "తెగులు ప్రమాదం", "అధిక ప్రమాదం", "రోగ్ ప్రమాదం", "रोग जोखिम", "उच्च जोखिम"]):
            return INTENT_DISEASE_RISK

        if any(term in q for term in ["treatment", "cure", "spray", "manage", "control", "fungicide", "bactericide", "remedy", "available for", "నివారణ", "చికిత్స", "మందు", "స్ప్రే", "ఉపాయం", "సలహా", "उपचार", "दवा", "स्प्रे", "इलाज", "नियंत्रण"]):
            return INTENT_TREATMENT

        if any(term in q for term in ["weather", "temperature", "humidity", "rainfall", "climate", "monsoon", "weather condition", "వాతావరణం", "తేమ", "ఉష్ణోగ్రత", "వర్షం", "मौसम", "तापमान", "आर्द्रता", "बारिश"]):
            return INTENT_WEATHER_RISK

        if any(term in q for term in ["disease", "pathogen", "infection", "blight", "wilt", "mildew", "rot", "affect", "attack", "వ్యాధులు", "తెగులు", "సోకే రోగాలు", "వస్తాయి", "రోగాలు", "बीमारियां", "बीमारियाँ", "बीमारी", "रोग", "झुलसा", "फसल रोग"]):
            return INTENT_CROP_DISEASE

        # 2. Semantic Embedding Cosine Matcher (Fallback if wording is novel)
        if self.encoder and self._anchor_embeddings:
            try:
                q_emb = self.encoder.encode([query], normalize_embeddings=True)[0]
                best_intent = INTENT_GENERAL
                best_score = -1.0
                for intent, emb_matrix in self._anchor_embeddings.items():
                    sims = np.dot(emb_matrix, q_emb)
                    max_sim = float(np.max(sims))
                    if max_sim > best_score:
                        best_score = max_sim
                        best_intent = intent
                if best_score > 0.55:
                    return best_intent
            except Exception:
                pass

        return INTENT_GENERAL

intent_detector = IntentDetector()

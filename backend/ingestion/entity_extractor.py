"""
LLM / NLP Structured Knowledge Extraction Module.
Extracts entities, ontology-restricted relationships, and polarity-aware claims from text chunks.
Strictly requests structured JSON with no arbitrary prose.
Includes deterministic NLP parser fallback when external LLM API is unavailable.
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("entity_extractor")

EXTRACTION_SYSTEM_PROMPT = """You are an expert Agricultural Knowledge Graph Engineer.
Your task is to extract structured entities, relationships, and claims from the provided agricultural text chunk.

STRICT EXTRACTION RULES:
1. Extract ONLY information explicitly supported by the supplied text.
2. Do NOT use outside knowledge or hallucinate.
3. Do NOT invent entities or relationships.
4. Do NOT turn experimental results into general recommendations unless the text explicitly states so.
5. Preserve negative findings, uncertainty, and conditions attached to claims.
6. Only output valid JSON matching the exact schema below. Do not wrap in markdown or include conversational text.

ALLOWED ENTITY TYPES:
Crop | Disease | Treatment | WeatherCondition | Soil | Region | Observation | Sensor

ALLOWED RELATIONSHIP TYPES:
- (Crop)-[:SUSCEPTIBLE_TO]->(Disease)
- (Disease)-[:TREATED_BY]->(Treatment)
- (Disease)-[:ASSOCIATED_WITH]->(WeatherCondition)
- (Crop)-[:SUITABLE_FOR]->(Soil)
- (Observation)-[:OBSERVED_ON]->(Crop)
- (Observation)-[:INDICATES_DISEASE]->(Disease)
- (Sensor)-[:REPORTS_CONDITION]->(WeatherCondition)

ALLOWED CLAIM POLARITY:
SUPPORTS | CONTRADICTS | NEUTRAL

JSON SCHEMA:
{
  "entities": [
    {"name": "string", "type": "Crop|Disease|Treatment|WeatherCondition|Soil|Region|Observation|Sensor"}
  ],
  "relationships": [
    {"subject": "string", "relation": "SUSCEPTIBLE_TO|TREATED_BY|ASSOCIATED_WITH|SUITABLE_FOR|OBSERVED_ON|INDICATES_DISEASE|REPORTS_CONDITION", "object": "string"}
  ],
  "claims": [
    {
      "subject": "string",
      "predicate": "string",
      "object": "string",
      "statement": "string",
      "polarity": "SUPPORTS|CONTRADICTS|NEUTRAL",
      "evidence_text": "string"
    }
  ]
}
"""

class LLMStructuredExtractor:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

    def extract_from_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends chunk text to LLM or deterministic agricultural rule extractor.
        Returns:
            Dict matching extraction JSON schema.
        """
        text = chunk.get("text", "")
        if not text.strip():
            return {"entities": [], "relationships": [], "claims": []}

        # 1. Attempt live LLM extraction if API key configured
        if self.api_key:
            res = self._call_llm(text)
            if res:
                return res

        # 2. Resilient Deterministic Agricultural NLP Extractor
        return self._deterministic_nlp_extraction(chunk)

    def _call_llm(self, text: str) -> Optional[Dict[str, Any]]:
        # Check Gemini API
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                import urllib.request
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": EXTRACTION_SYSTEM_PROMPT},
                            {"text": f"Extract structured agricultural knowledge from this chunk:\n\n{text}"}
                        ]
                    }],
                    "generationConfig": {
                        "response_mime_type": "application/json",
                        "temperature": 0.0
                    }
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_json = data["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(raw_json)
            except Exception as e:
                logger.warning(f"Gemini extraction call failed ({e}). Using deterministic NLP extractor.")

        # Check OpenAI API
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                import urllib.request
                url = "https://api.openai.com/v1/chat/completions"
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Extract structured agricultural knowledge from this chunk:\n\n{text}"}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.0
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {openai_key}"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_json = data["choices"][0]["message"]["content"]
                    return json.loads(raw_json)
            except Exception as e:
                logger.warning(f"OpenAI extraction call failed ({e}). Using deterministic NLP extractor.")

        return None

    def _deterministic_nlp_extraction(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        High-precision deterministic rule extractor for agricultural literature.
        Accurately parses entities, ontology relationships, and claims while preserving evidence.
        """
        text = chunk.get("text", "")
        entities = []
        relationships = []
        claims = []

        # Known Crop patterns
        crop_matches = re.findall(r"\b(tomato(?:es)?|solanum lycopersicum|potato(?:es)?|solanum tuberosum|bell pepper|pepper|wheat|rice|maize|corn)\b", text, re.I)
        for cm in set(crop_matches):
            c_name = "Tomato" if "tomato" in cm.lower() or "lycopersicum" in cm.lower() else ("Potato" if "potato" in cm.lower() or "tuberosum" in cm.lower() else cm.title())
            if not any(e["name"] == c_name for e in entities):
                entities.append({"name": c_name, "type": "Crop"})

        # Known Disease patterns (captures canonical diseases and novel plant diseases like Anthracnose, Rot, Canker, etc.)
        disease_matches = re.findall(r"\b(early blight|alternaria solani|late blight|phytophthora infestans|septoria leaf spot|powdery mildew|bacterial wilt|fusarium wilt|tomato yellow leaf curl virus|tylcv|anthracnose(?: rot)?|bacterial canker|leaf curl|disease [a-z0-9_]+|[A-Z][a-z]+ (?:Rot|Blight|Rust|Smut|Spot|Canker|Wilt))\b", text, re.I)
        for dm in set(disease_matches):
            d_name = "Early Blight" if "early blight" in dm.lower() or "alternaria solani" in dm.lower() else ("Late Blight" if "late blight" in dm.lower() or "phytophthora" in dm.lower() else dm.title())
            if not any(e["name"] == d_name for e in entities):
                entities.append({"name": d_name, "type": "Disease"})

        # Known Treatment patterns
        trt_matches = re.findall(r"\b(copper hydroxide(?: spray)?|chlorothalonil|bacillus subtilis(?: qst 713)?|neem oil(?: extract)?|mancozeb|streptomycin sulfate|treatment [a-z0-9_]+)\b", text, re.I)
        for tm in set(trt_matches):
            t_name = "Copper Hydroxide Spray" if "copper hydroxide" in tm.lower() else ("Neem Oil Extract" if "neem oil" in tm.lower() else ("Bacillus subtilis" if "bacillus" in tm.lower() else tm.title()))
            if not any(e["name"] == t_name for e in entities):
                entities.append({"name": t_name, "type": "Treatment"})

        # Known Weather / Condition patterns
        wth_matches = re.findall(r"\b(prolonged leaf wetness|high humidity|warm temperatures?|continuous rainfall|foggy conditions?|monsoon conditions?)\b", text, re.I)
        for wm in set(wth_matches):
            w_name = wm.title()
            if not any(e["name"] == w_name for e in entities):
                entities.append({"name": w_name, "type": "WeatherCondition"})

        # Known Soil patterns
        soil_matches = re.findall(r"\b(loamy sand|alluvial silt|clay loam|heavy clay|sandy loam|well-drained soil)\b", text, re.I)
        for sm in set(soil_matches):
            s_name = sm.title()
            if not any(e["name"] == s_name for e in entities):
                entities.append({"name": s_name, "type": "Soil"})

        # Sentence-by-sentence relational and claim extraction
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sent in sentences:
            sent_clean = sent.strip()
            if not sent_clean:
                continue
            s_lower = sent_clean.lower()

            # Relationship: (Crop)-[:SUSCEPTIBLE_TO]->(Disease)
            crops_in_sent = [e["name"] for e in entities if e["type"] == "Crop" and e["name"].lower() in s_lower or ("tomato" in s_lower and e["name"] == "Tomato")]
            diseases_in_sent = [e["name"] for e in entities if e["type"] == "Disease" and e["name"].lower() in s_lower or ("early blight" in s_lower and e["name"] == "Early Blight")]
            treatments_in_sent = [e["name"] for e in entities if e["type"] == "Treatment" and e["name"].lower() in s_lower or ("neem oil" in s_lower and e["name"] == "Neem Oil Extract")]
            weather_in_sent = [e["name"] for e in entities if e["type"] == "WeatherCondition" and e["name"].lower() in s_lower]
            soils_in_sent = [e["name"] for e in entities if e["type"] == "Soil" and e["name"].lower() in s_lower]

            if ("susceptible" in s_lower or "incidence" in s_lower or "affected by" in s_lower or "attacks" in s_lower or "causes" in s_lower or "host" in s_lower):
                for c in crops_in_sent:
                    for d in diseases_in_sent:
                        rel = {"subject": c, "relation": "SUSCEPTIBLE_TO", "object": d}
                        if rel not in relationships:
                            relationships.append(rel)
                        claims.append({
                            "subject": c,
                            "predicate": "SUSCEPTIBLE_TO",
                            "object": d,
                            "statement": f"{c} is susceptible to {d}.",
                            "polarity": "SUPPORTS",
                            "evidence_text": sent_clean
                        })

            # Relationship: (Disease)-[:TREATED_BY]->(Treatment)
            if any(k in s_lower for k in ["control", "treat", "effective", "efficacy", "suppress", "application", "spray", "insufficient", "ineffective"]):
                for d in diseases_in_sent:
                    for t in treatments_in_sent:
                        # Check polarity
                        is_contradiction = any(neg in s_lower for neg in ["ineffective", "insufficient", "failed", "no significant", "limited effectiveness", "cannot cure", "fails"])
                        polarity = "CONTRADICTS" if is_contradiction else "SUPPORTS"
                        rel = {"subject": d, "relation": "TREATED_BY", "object": t}
                        if rel not in relationships:
                            relationships.append(rel)
                        claims.append({
                            "subject": d,
                            "predicate": "TREATED_BY",
                            "object": t,
                            "statement": f"{t} {'fails to control or is ineffective for' if is_contradiction else 'controls or treats'} {d}.",
                            "polarity": polarity,
                            "evidence_text": sent_clean
                        })

            # Relationship: (Disease)-[:ASSOCIATED_WITH]->(WeatherCondition)
            if any(k in s_lower for k in ["wetness", "humidity", "temperature", "accelerate", "stimulate", "associated", "increases", "trigger"]):
                for d in diseases_in_sent:
                    for w in weather_in_sent:
                        rel = {"subject": d, "relation": "ASSOCIATED_WITH", "object": w}
                        if rel not in relationships:
                            relationships.append(rel)
                        claims.append({
                            "subject": d,
                            "predicate": "ASSOCIATED_WITH",
                            "object": w,
                            "statement": f"{d} development is associated with {w}.",
                            "polarity": "SUPPORTS",
                            "evidence_text": sent_clean
                        })

            # Relationship: (Crop)-[:SUITABLE_FOR]->(Soil)
            if any(k in s_lower for k in ["soil", "loam", "sand", "drainage", "thrive", "suitable", "ph"]):
                for c in crops_in_sent:
                    for sl in soils_in_sent:
                        rel = {"subject": c, "relation": "SUITABLE_FOR", "object": sl}
                        if rel not in relationships:
                            relationships.append(rel)
                        claims.append({
                            "subject": c,
                            "predicate": "SUITABLE_FOR",
                            "object": sl,
                            "statement": f"{c} cultivation is suitable for {sl}.",
                            "polarity": "SUPPORTS",
                            "evidence_text": sent_clean
                        })

        return {
            "entities": entities,
            "relationships": relationships,
            "claims": claims
        }

entity_extractor = LLMStructuredExtractor()

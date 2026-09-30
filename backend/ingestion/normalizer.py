"""
Entity Normalizer Module.
Normalizes extracted raw entity names against existing knowledge graph entities using:
1. Exact string matching (case-insensitive)
2. Domain synonym / alias dictionaries
3. Embedding cosine similarity (SentenceTransformer)
Preserves raw names as aliases and generates persistent canonical IDs.
"""

import re
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from backend.graph.service import graph_service

logger = logging.getLogger("entity_normalizer")

# Canonical Aliases Map
ENTITY_ALIASES = {
    "Tomato": ["tomato", "tomato crop", "solanum lycopersicum", "tomatoes", "lycopersicon esculentum"],
    "Potato": ["potato", "potato crop", "solanum tuberosum", "potatoes"],
    "Bell Pepper": ["bell pepper", "capsicum", "pepper", "capsicum annuum"],
    "Wheat": ["wheat", "triticum aestivum", "wheat crop"],
    "Early Blight": ["early blight", "alternaria solani", "target spot of tomato", "alternaria leaf blight"],
    "Late Blight": ["late blight", "phytophthora infestans", "potato late blight"],
    "Septoria Leaf Spot": ["septoria leaf spot", "septoria lycopersici"],
    "Copper Hydroxide Spray": ["copper hydroxide", "copper hydroxide spray", "kocide", "copper fungicide"],
    "Chlorothalonil Fungicide": ["chlorothalonil", "chlorothalonil fungicide", "bravo"],
    "Bacillus subtilis": ["bacillus subtilis", "bacillus subtilis qst 713", "serenade biofungicide"],
    "Neem Oil Extract": ["neem oil", "neem oil extract", "azadirachtin", "botanical neem spray"],
    "Humid Warm Monsoon": ["prolonged leaf wetness", "high humidity", "warm monsoon", "humid warm monsoon", "wet foliage"],
    "Loamy Sand": ["loamy sand", "sandy loam", "well-drained loam"],
    "Alluvial Silt": ["alluvial silt", "silt loam"]
}

class EntityNormalizer:
    def __init__(self):
        self.encoder = None

    def attach_encoder(self, encoder):
        self.encoder = encoder

    def normalize_entity(self, raw_entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes an extracted entity against the knowledge graph.
        Returns:
            Normalized entity dict with canonical id, canonical name, label, and alias metadata.
        """
        raw_name = raw_entity.get("name", "").strip()
        raw_type = raw_entity.get("type", "General").capitalize()
        name_lower = raw_name.lower()

        # Step 1: Exact match with existing graph nodes
        for node_id, node in graph_service.nodes.items():
            if node["name"].lower() == name_lower:
                return {
                    "id": node_id,
                    "name": node["name"],
                    "label": node["label"],
                    "is_new": False,
                    "matched_by": "exact_name",
                    "original_name": raw_name
                }

        # Step 2: Alias dictionary lookup
        for canonical, aliases in ENTITY_ALIASES.items():
            if name_lower == canonical.lower() or any(a in name_lower or name_lower in a for a in aliases):
                # Check if this canonical entity exists in the graph
                node = next((n for n in graph_service.nodes.values() if n["name"].lower() == canonical.lower()), None)
                if node:
                    return {
                        "id": node["id"],
                        "name": node["name"],
                        "label": node["label"],
                        "is_new": False,
                        "matched_by": "alias_lookup",
                        "original_name": raw_name
                    }
                else:
                    # Known canonical but not yet in graph
                    return {
                        "id": self._generate_new_id(raw_type, canonical),
                        "name": canonical,
                        "label": raw_type,
                        "is_new": True,
                        "matched_by": "alias_new_entity",
                        "original_name": raw_name
                    }

        # Step 3: Semantic similarity matching via embeddings
        if self.encoder and graph_service.nodes:
            try:
                candidate_nodes = list(graph_service.nodes.values())
                candidate_names = [n["name"] for n in candidate_nodes]
                c_embs = self.encoder.encode(candidate_names, normalize_embeddings=True)
                q_emb = self.encoder.encode([raw_name], normalize_embeddings=True)[0]
                sims = np.dot(c_embs, q_emb)
                best_idx = int(np.argmax(sims))
                best_sim = float(sims[best_idx])
                if best_sim > 0.88:  # Strict confidence threshold to avoid false merges
                    matched_node = candidate_nodes[best_idx]
                    return {
                        "id": matched_node["id"],
                        "name": matched_node["name"],
                        "label": matched_node["label"],
                        "is_new": False,
                        "matched_by": f"semantic_sim_{best_sim:.2f}",
                        "original_name": raw_name
                    }
            except Exception as e:
                logger.warning(f"Semantic similarity normalization error: {e}")

        # Step 4: If not merged, create a clean new entity
        clean_name = raw_name.title()
        new_id = self._generate_new_id(raw_type, clean_name)
        return {
            "id": new_id,
            "name": clean_name,
            "label": raw_type if raw_type in ["Crop", "Disease", "Treatment", "WeatherCondition", "Soil", "Observation", "Sensor", "Source", "Claim"] else "Entity",
            "is_new": True,
            "matched_by": "new_entity",
            "original_name": raw_name
        }

    def _generate_new_id(self, label: str, name: str) -> str:
        prefix_map = {
            "Crop": "CROP",
            "Disease": "DIS",
            "Treatment": "TRT",
            "Weathercondition": "WTH",
            "Soil": "SOIL",
            "Observation": "OBS",
            "Sensor": "SENSOR",
            "Claim": "CLM",
            "Source": "DOC"
        }
        prefix = prefix_map.get(label.capitalize(), "ENT")
        slug = re.sub(r"[^A-Za-z0-9]+", "_", name.upper()).strip("_")
        return f"{prefix}_{slug[:16]}"

entity_normalizer = EntityNormalizer()

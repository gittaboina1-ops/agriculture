import time
import json
import os
import sys
from typing import Dict, Any, List, Optional
import logging
from backend.graph.service import graph_service
from backend.provenance.tracker import provenance_tracker
from backend.conflict.engine import conflict_engine
from backend.validation.validator import validation_service
from backend.services.mongo_service import mongo_service
from backend.retrieval.intent import intent_detector
from backend.services.llm_service import llm_service

# Suppress noisy HuggingFace/transformers output during CLI usage
os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logger = logging.getLogger("retrieval_service")

class SemanticRetrievalService:
    def __init__(self):
        self.encoder = None
        self.model_name = "all-MiniLM-L6-v2"
        self.model_status = "unloaded"
        self._init_encoder()
        self.entity_catalog = []
        self._build_entity_catalog()

    def _init_encoder(self):
        # Redirect stderr temporarily to hide Huggingface tqdm download bars in terminal
        old_stderr = sys.stderr
        try:
            with open(os.devnull, "w") as devnull:
                sys.stderr = devnull
                from sentence_transformers import SentenceTransformer
                self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", local_files_only=True)
            self.model_status = "loaded"
            intent_detector.attach_encoder(self.encoder)
            from backend.ingestion.semantic_index import semantic_index
            from backend.ingestion.normalizer import entity_normalizer
            semantic_index.attach_encoder(self.encoder)
            entity_normalizer.attach_encoder(self.encoder)
        except Exception:
            try:
                with open(os.devnull, "w") as devnull:
                    sys.stderr = devnull
                    from sentence_transformers import SentenceTransformer
                    self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
                self.model_status = "loaded"
                intent_detector.attach_encoder(self.encoder)
                from backend.ingestion.semantic_index import semantic_index
                from backend.ingestion.normalizer import entity_normalizer
                semantic_index.attach_encoder(self.encoder)
                entity_normalizer.attach_encoder(self.encoder)
            except Exception:
                self.encoder = None
                self.model_status = "fallback_rules"
        finally:
            sys.stderr = old_stderr

    def _build_entity_catalog(self):
        self.entity_catalog.clear()
        for node_id, node in graph_service.nodes.items():
            self.entity_catalog.append({
                "id": node_id,
                "label": node["label"],
                "name": node["name"],
                "text": f"{node['name']} {node['label']} {node.get('properties', {}).get('description', '')}"
            })

    def match_entities(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        matched = []

        # 1. Exact string / case-insensitive entity match
        for ent in self.entity_catalog:
            ent_name_lower = ent["name"].lower()
            if ent_name_lower in query_lower:
                if not any(m["id"] == ent["id"] for m in matched):
                    matched.append({**ent, "score": 1.0, "match_type": "exact"})

        # 2. Agricultural entity aliases & synonyms (English, Telugu, Hindi, transliterations)
        # Tomato aliases
        if any(term in query_lower for term in ["tomato", "టమోటా", "టమాటా", "టమాట", "टमाटर"]) and not any(m["name"].lower() == "tomato" for m in matched):
            ent = next((e for e in self.entity_catalog if e["id"] == "CROP_001"), None)
            if ent:
                matched.append({**ent, "score": 1.0, "match_type": "crop_match"})

        # Potato aliases
        if any(term in query_lower for term in ["potato", "బంగాళాదుంప", "ఆలుగడ్డ", "आलू"]) and not any(m["name"].lower() == "potato" for m in matched):
            ent = next((e for e in self.entity_catalog if e["id"] == "CROP_002"), None)
            if ent:
                matched.append({**ent, "score": 1.0, "match_type": "crop_match"})

        # Pepper aliases
        if any(term in query_lower for term in ["pepper", "bell pepper", "క్యాప్సికం", "మిరప", "शिमला मिर्च", "मिर्च"]) and not any(m["name"].lower() == "bell pepper" for m in matched):
            ent = next((e for e in self.entity_catalog if e["id"] == "CROP_003"), None)
            if ent:
                matched.append({**ent, "score": 1.0, "match_type": "crop_match"})

        # Wheat aliases
        if any(term in query_lower for term in ["wheat", "గోధుమ", "गेहूं"]) and not any(m["name"].lower() == "wheat" for m in matched):
            ent = next((e for e in self.entity_catalog if e["id"] == "CROP_004"), None)
            if ent:
                matched.append({**ent, "score": 1.0, "match_type": "crop_match"})

        # Soil aliases
        if any(term in query_lower for term in ["soil", "మట్టి", "నేల", "భూమి", "मिट्टी", "जमीन"]):
            for sid in ["SOIL_001", "SOIL_004"]:
                ent = next((e for e in self.entity_catalog if e["id"] == sid), None)
                if ent and not any(m["id"] == sid for m in matched):
                    matched.append({**ent, "score": 0.90, "match_type": "soil_entity"})

        # Late Blight aliases
        if any(term in query_lower for term in ["late blight", "లేట్ బ్లైట్", "పచేతి", "पछेती झुलसा"]):
            ent = next((e for e in self.entity_catalog if e["id"] == "DIS_002"), None)
            if ent and not any(m["id"] == "DIS_002" for m in matched):
                matched.append({**ent, "score": 1.0, "match_type": "disease_match"})

        # Early Blight aliases
        if any(term in query_lower for term in ["early blight", "ముందస్తు తెగులు", "అగేతి", "अगेती झुलसा"]) or ("blight" in query_lower and "late" not in query_lower):
            ent = next((e for e in self.entity_catalog if e["id"] == "DIS_001"), None)
            if ent and not any(m["id"] == "DIS_001" for m in matched):
                matched.append({**ent, "score": 0.95, "match_type": "disease_match"})

        # Treatment aliases
        if any(term in query_lower for term in ["treatment", "spray", "control", "copper", "మందు", "స్ప్రే", "నివారణ", "చికిత్స", "उपचार", "दवा", "स्प्रे", "रोकथाम"]):
            for tid in ["TRT_001", "TRT_002", "TRT_003"]:
                ent = next((e for e in self.entity_catalog if e["id"] == tid), None)
                if ent and not any(m["id"] == tid for m in matched):
                    matched.append({**ent, "score": 0.85, "match_type": "treatment_match"})

        # Neem aliases
        if any(term in query_lower for term in ["neem", "botanical", "వేప", "వేపనూనె", "నీమ్", "नीम"]):
            ent = next((e for e in self.entity_catalog if e["id"] == "TRT_005"), None)
            if ent and not any(m["id"] == "TRT_005" for m in matched):
                matched.append({**ent, "score": 0.98, "match_type": "conflict_entity"})

        # Default fallback anchor
        if not matched:
            ent = next((e for e in self.entity_catalog if e["id"] == "CROP_001"), None)
            if ent:
                matched.append({**ent, "score": 0.70, "match_type": "default_anchor"})

        return matched

    def execute_farmer_query(self, query_text: str) -> Dict[str, Any]:
        start_time = time.time()
        q_lower = query_text.lower().strip()

        # Rebuild entity catalog so newly ingested nodes are immediately searchable
        self._build_entity_catalog()

        # Step 1: Detect Query Intent
        intent = intent_detector.detect_intent(query_text)

        # Step 2: Identify Entities
        matched_entities = self.match_entities(query_text)
        matched_ids = [e["id"] for e in matched_entities]
        matched_crop = next((e["name"] for e in matched_entities if e["label"] == "Crop"), "Tomato")
        crop_node_id = next((e["id"] for e in matched_entities if e["label"] == "Crop"), "CROP_001")

        # Step 3: Intent-Filtered Knowledge Graph Traversal
        subgraph_nodes = []
        subgraph_edges = []
        relevant_soil_records = []

        if intent == "SOIL_SUITABILITY":
            for edge in graph_service.edges:
                if edge["source"] == crop_node_id and edge["relationship"] == "SUITABLE_FOR":
                    subgraph_edges.append(edge)
                    target_soil = graph_service.nodes.get(edge["target"])
                    if target_soil and target_soil not in relevant_soil_records:
                        relevant_soil_records.append(target_soil)

            crop_node = graph_service.nodes.get(crop_node_id)
            if crop_node:
                subgraph_nodes.append(crop_node)
            for s in relevant_soil_records:
                if s not in subgraph_nodes:
                    subgraph_nodes.append(s)

        elif intent == "CROP_DISEASE":
            for edge in graph_service.edges:
                if edge["source"] == crop_node_id and edge["relationship"] == "SUSCEPTIBLE_TO":
                    subgraph_edges.append(edge)
                    target_dis = graph_service.nodes.get(edge["target"])
                    if target_dis and target_dis not in subgraph_nodes:
                        subgraph_nodes.append(target_dis)
            crop_node = graph_service.nodes.get(crop_node_id)
            if crop_node and crop_node not in subgraph_nodes:
                subgraph_nodes.append(crop_node)

        elif intent == "TREATMENT":
            dis_id = "DIS_001" if "early" in q_lower or "tomato" in q_lower else "DIS_002"
            for edge in graph_service.edges:
                if edge["source"] == dis_id and edge["relationship"] == "TREATED_BY":
                    subgraph_edges.append(edge)
                    target_trt = graph_service.nodes.get(edge["target"])
                    if target_trt and target_trt not in subgraph_nodes:
                        subgraph_nodes.append(target_trt)
            dis_node = graph_service.nodes.get(dis_id)
            if dis_node and dis_node not in subgraph_nodes:
                subgraph_nodes.append(dis_node)

        elif intent == "CONFLICT":
            trt_id = "TRT_005"
            for edge in graph_service.edges:
                if edge["target"] == trt_id or edge["source"] == trt_id or edge["source"] == "CLM_004":
                    subgraph_edges.append(edge)
            subgraph_nodes = [n for n in graph_service.nodes.values() if n["id"] in ["TRT_005", "CLM_004", "DOC_003", "DOC_004"]]

        elif intent == "DATA_QUALITY":
            for edge in graph_service.edges:
                if "SENSOR" in edge["source"]:
                    subgraph_edges.append(edge)
            subgraph_nodes = [n for n in graph_service.nodes.values() if n["label"] in ["Sensor", "WeatherCondition"]]

        elif intent == "DISEASE_RISK":
            # Focused DISEASE_RISK traversal: strictly isolates the requested crop's active risk factors.
            # Explicitly excludes unrelated crops (e.g. Potato), general treatments, and unrelated soil suitability.
            target_dis_id = "DIS_001" if crop_node_id == "CROP_001" else ("DIS_002" if crop_node_id == "CROP_002" else "DIS_001")
            
            # (Crop)-[:SUSCEPTIBLE_TO]->(Disease)
            for edge in graph_service.edges:
                if edge["source"] == crop_node_id and edge["target"] == target_dis_id and edge["relationship"] == "SUSCEPTIBLE_TO":
                    subgraph_edges.append(edge)

            # (Disease)-[:ASSOCIATED_WITH]->(WeatherCondition)
            for edge in graph_service.edges:
                if edge["source"] == target_dis_id and edge["relationship"] == "ASSOCIATED_WITH":
                    subgraph_edges.append(edge)

            # (Observation)-[:OBSERVED_ON]->(Crop) & (Observation)-[:INDICATES_DISEASE]->(Disease)
            for edge in graph_service.edges:
                if edge["relationship"] in ["OBSERVED_ON", "INDICATES_DISEASE"]:
                    if edge["target"] in [crop_node_id, target_dis_id]:
                        subgraph_edges.append(edge)

            # (Sensor)-[:REPORTS_CONDITION]->(WeatherCondition)
            for edge in graph_service.edges:
                if edge["relationship"] == "REPORTS_CONDITION" and edge["target"] == "WTH_001":
                    subgraph_edges.append(edge)

            # Assemble strictly relevant node objects
            node_ids_in_edges = set()
            for edge in subgraph_edges:
                node_ids_in_edges.add(edge["source"])
                node_ids_in_edges.add(edge["target"])

            subgraph_nodes = [graph_service.nodes[nid] for nid in node_ids_in_edges if nid in graph_service.nodes]

        else: # WEATHER_RISK, GENERAL
            raw_sub = graph_service.get_subgraph_for_entities(matched_ids)
            # Ensure unrelated crops are not leaked
            subgraph_nodes = [n for n in raw_sub["nodes"] if n["id"] != "CROP_002" or crop_node_id == "CROP_002"]
            subgraph_edges = [e for e in raw_sub["edges"] if e["source"] != "CROP_002" and e["target"] != "CROP_002" or crop_node_id == "CROP_002"]

        subgraph = {
            "nodes": subgraph_nodes,
            "edges": subgraph_edges
        }

        # Step 4: Semantic Chunk Search (Hybrid Graph + Vector Evidence)
        from backend.ingestion.semantic_index import semantic_index
        semantic_chunks = semantic_index.search_similar(query_text, top_k=3)
        relevant_evidence = []
        relevant_sources = []

        # Connect semantic chunk sources
        for schunk in semantic_chunks:
            did = schunk.get("document_id")
            if did:
                src = provenance_tracker.get_source(did)
                if src and not any(s["source_id"] == src["source_id"] for s in relevant_sources):
                    relevant_sources.append(src)

        for edge in subgraph_edges:
            prov_id = edge.get("properties", {}).get("provenance")
            if prov_id:
                sids = [s.strip() for s in prov_id.replace("vs", ",").split(",") if s.strip()]
                for sid in sids:
                    src = provenance_tracker.get_source(sid)
                    if src and not any(s["source_id"] == src["source_id"] for s in relevant_sources):
                        relevant_sources.append(src)

            src_node = graph_service.nodes.get(edge["source"])
            tgt_node = graph_service.nodes.get(edge["target"])
            if src_node and tgt_node:
                relevant_evidence.append({
                    "subject": src_node["name"],
                    "relationship": edge["relationship"],
                    "object": tgt_node["name"],
                    "details": edge.get("properties", {}),
                    "provenance": prov_id or "Agricultural Knowledge Graph"
                })

        # Attach specific verified documents based on intent
        if intent == "SOIL_SUITABILITY":
            doc5 = provenance_tracker.get_source("DOC_005")
            if doc5 and not any(s["source_id"] == "DOC_005" for s in relevant_sources):
                relevant_sources.append(doc5)
        elif intent in ["CONFLICT", "TREATMENT"]:
            for did in ["DOC_003", "DOC_004"]:
                d = provenance_tracker.get_source(did)
                if d and not any(s["source_id"] == did for s in relevant_sources):
                    relevant_sources.append(d)
        elif intent in ["DISEASE_RISK", "CROP_DISEASE", "WEATHER_RISK"]:
            for did in ["DOC_001", "DOC_007"]:
                d = provenance_tracker.get_source(did)
                if d and not any(s["source_id"] == did for s in relevant_sources):
                    relevant_sources.append(d)

        # Step 5: Conflict Detection (Strictly scoped)
        active_conflicts = []
        all_conflicts = conflict_engine.evaluate_claims(provenance_tracker.claims, provenance_tracker.sources)
        if intent in ["CONFLICT", "TREATMENT", "DISEASE_RISK", "GENERAL"]:
            active_conflicts = all_conflicts

        # Step 6: Sensor Validation Check
        sensors_file = os.path.join("data", "sensors.json")
        data_quality_warnings = []
        if os.path.exists(sensors_file):
            with open(sensors_file, "r") as f:
                raw_sensors = json.load(f)
                val_res = validation_service.process_readings(raw_sensors)
                if intent in ["DATA_QUALITY", "DISEASE_RISK", "GENERAL"]:
                    for inv in val_res["invalid_records"]:
                        data_quality_warnings.append({
                            "reading_id": inv.get("reading_id"),
                            "sensor_id": inv.get("sensor_id"),
                            "metric": inv.get("metric"),
                            "rejected_value": f"{inv.get('value')} {inv.get('unit', '')}",
                            "reason": inv.get("anomaly_reason"),
                            "action_taken": inv.get("action_taken", "Excluded from reasoning")
                        })

        # Step 7: Build Evidence Context & Generate LLM Answer
        context_payload = {
            "query": query_text,
            "intent": intent,
            "matched_crop": matched_crop,
            "entities": matched_entities,
            "graph_evidence": relevant_evidence,
            "sources": relevant_sources,
            "conflicts": active_conflicts,
            "data_quality_warnings": data_quality_warnings,
            "soil_records": relevant_soil_records,
            "semantic_chunks": semantic_chunks
        }

        llm_response = llm_service.generate_grounded_answer(query_text, intent, context_payload)

        latency = round((time.time() - start_time) * 1000, 2)

        evaluation_metrics = {
            "query_latency_ms": latency,
            "intent_detected": intent,
            "entities_extracted": len(matched_entities),
            "graph_nodes_retrieved": len(subgraph["nodes"]),
            "graph_edges_retrieved": len(subgraph["edges"]),
            "sources_cited": len(relevant_sources),
            "conflicts_flagged": len(active_conflicts),
            "invalid_sensor_records_rejected": len(data_quality_warnings),
            "provenance_coverage_pct": 100.0 if relevant_sources else 0.0
        }

        response = {
            "query": query_text,
            "intent": intent,
            "matched_crop": matched_crop,
            "entities": matched_entities,
            "agricultural_insight": llm_response["agricultural_insight"],
            "relevant_factors": llm_response["relevant_factors"],
            "evidence": relevant_evidence,
            "sources": relevant_sources,
            "conflicts": active_conflicts,
            "data_quality_warnings": data_quality_warnings,
            "subgraph": subgraph,
            "evaluation_metrics": evaluation_metrics,
            "generation_mode": llm_response.get("mode", "grounded_rule_engine"),
            "provider": llm_response.get("provider", "fallback"),
            "model": llm_response.get("model", None),
            "fallback_reason": llm_response.get("fallback_reason", None)
        }

        mongo_service.log_query({
            "query": query_text,
            "intent": intent,
            "matched_crop": matched_crop,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latency_ms": latency,
            "conflicts_count": len(active_conflicts),
            "warnings_count": len(data_quality_warnings)
        })

        return response

retrieval_service = SemanticRetrievalService()

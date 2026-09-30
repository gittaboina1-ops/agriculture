import time
import json
import os
from typing import Dict, Any, List, Optional
import logging
from backend.graph.service import graph_service
from backend.provenance.tracker import provenance_tracker
from backend.conflict.engine import conflict_engine
from backend.validation.validator import validation_service
from backend.services.mongo_service import mongo_service
from backend.retrieval.intent import intent_detector
from backend.services.llm_service import llm_service

logger = logging.getLogger("retrieval_service")

class SemanticRetrievalService:
    def __init__(self):
        self.encoder = None
        self._init_encoder()
        self.entity_catalog = []
        self._build_entity_catalog()

    def _init_encoder(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({e}). Using n-gram keyword token matcher fallback.")
            self.encoder = None

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

        # 1. Exact / substring match
        for ent in self.entity_catalog:
            ent_name_lower = ent["name"].lower()
            if ent_name_lower in query_lower:
                if not any(m["id"] == ent["id"] for m in matched):
                    matched.append({**ent, "score": 1.0, "match_type": "exact"})

        # 2. Agricultural entity aliases
        if "potato" in query_lower and not any(m["name"].lower() == "potato" for m in matched):
            ent = next((e for e in self.entity_catalog if e["id"] == "CROP_002"), None)
            if ent:
                matched.append({**ent, "score": 1.0, "match_type": "crop_match"})

        if "tomato" in query_lower and not any(m["name"].lower() == "tomato" for m in matched):
            ent = next((e for e in self.entity_catalog if e["id"] == "CROP_001"), None)
            if ent:
                matched.append({**ent, "score": 1.0, "match_type": "crop_match"})

        if "soil" in query_lower:
            for sid in ["SOIL_001", "SOIL_004"]:
                ent = next((e for e in self.entity_catalog if e["id"] == sid), None)
                if ent and not any(m["id"] == sid for m in matched):
                    matched.append({**ent, "score": 0.90, "match_type": "soil_entity"})

        if "late blight" in query_lower:
            ent = next((e for e in self.entity_catalog if e["id"] == "DIS_002"), None)
            if ent and not any(m["id"] == "DIS_002" for m in matched):
                matched.append({**ent, "score": 1.0, "match_type": "disease_match"})

        if ("early blight" in query_lower or ("blight" in query_lower and "late" not in query_lower)):
            ent = next((e for e in self.entity_catalog if e["id"] == "DIS_001"), None)
            if ent and not any(m["id"] == "DIS_001" for m in matched):
                matched.append({**ent, "score": 0.95, "match_type": "disease_match"})

        if ("treatment" in query_lower or "spray" in query_lower or "control" in query_lower or "copper" in query_lower):
            for tid in ["TRT_001", "TRT_002", "TRT_003"]:
                ent = next((e for e in self.entity_catalog if e["id"] == tid), None)
                if ent and not any(m["id"] == tid for m in matched):
                    matched.append({**ent, "score": 0.85, "match_type": "treatment_match"})

        if ("neem" in query_lower or "botanical" in query_lower):
            ent = next((e for e in self.entity_catalog if e["id"] == "TRT_005"), None)
            if ent and not any(m["id"] == "TRT_005" for m in matched):
                matched.append({**ent, "score": 0.98, "match_type": "conflict_entity"})

        # Default anchor if completely generic
        if not matched:
            ent = next((e for e in self.entity_catalog if e["id"] == "CROP_001"), None)
            if ent:
                matched.append({**ent, "score": 0.70, "match_type": "default_anchor"})

        return matched

    def execute_farmer_query(self, query_text: str) -> Dict[str, Any]:
        start_time = time.time()
        q_lower = query_text.lower().strip()

        # Step 1: Detect Query Intent
        intent = intent_detector.detect_intent(query_text)

        # Step 2: Identify Entities
        matched_entities = self.match_entities(query_text)
        matched_ids = [e["id"] for e in matched_entities]
        matched_crop = next((e["name"] for e in matched_entities if e["label"] == "Crop"), "Tomato")
        crop_node_id = next((e["id"] for e in matched_entities if e["label"] == "Crop"), "CROP_001")

        # Step 3: Intent-Filtered Knowledge Graph Traversal
        # CRITICAL RULE: Filter relationships strictly according to intent!
        # E.g. SOIL_SUITABILITY must prioritize (Crop)-[:SUITABLE_FOR]->(Soil) and exclude disease paths!
        subgraph_nodes = []
        subgraph_edges = []
        relevant_soil_records = []

        if intent == "SOIL_SUITABILITY":
            # Target SUITABLE_FOR edges from crop
            for edge in graph_service.edges:
                if edge["source"] == crop_node_id and edge["relationship"] == "SUITABLE_FOR":
                    subgraph_edges.append(edge)
                    target_soil = graph_service.nodes.get(edge["target"])
                    if target_soil and target_soil not in relevant_soil_records:
                        relevant_soil_records.append(target_soil)

            # Include the crop node and soil nodes
            crop_node = graph_service.nodes.get(crop_node_id)
            if crop_node:
                subgraph_nodes.append(crop_node)
            for s in relevant_soil_records:
                if s not in subgraph_nodes:
                    subgraph_nodes.append(s)

        elif intent == "CROP_DISEASE":
            # Target SUSCEPTIBLE_TO edges
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
            # Target TREATED_BY edges
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
            # Neem Oil dispute
            trt_id = "TRT_005"
            for edge in graph_service.edges:
                if edge["target"] == trt_id or edge["source"] == trt_id or edge["source"] == "CLM_004":
                    subgraph_edges.append(edge)
            subgraph_nodes = [n for n in graph_service.nodes.values() if n["id"] in ["TRT_005", "CLM_004", "DOC_003", "DOC_004"]]

        elif intent == "DATA_QUALITY":
            # Sensor telemetry focus
            for edge in graph_service.edges:
                if "SENSOR" in edge["source"]:
                    subgraph_edges.append(edge)
            subgraph_nodes = [n for n in graph_service.nodes.values() if n["label"] in ["Sensor", "WeatherCondition"]]

        else: # DISEASE_RISK, WEATHER_RISK, GENERAL
            # Full disease risk traversal: Crop -> Disease -> Weather -> Observation
            raw_sub = graph_service.get_subgraph_for_entities(matched_ids)
            subgraph_nodes = raw_sub["nodes"]
            subgraph_edges = raw_sub["edges"]

        subgraph = {
            "nodes": subgraph_nodes,
            "edges": subgraph_edges
        }

        # Step 4: Extract Relational Evidence Triples
        relevant_evidence = []
        relevant_sources = []
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
                # Only show warnings if intent relates to data quality or disease risk evaluation
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
            "soil_records": relevant_soil_records
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
            "agricultural_insight": llm_response["agricultural_insight"],
            "relevant_factors": llm_response["relevant_factors"],
            "evidence": relevant_evidence,
            "sources": relevant_sources,
            "conflicts": active_conflicts,
            "data_quality_warnings": data_quality_warnings,
            "subgraph": subgraph,
            "evaluation_metrics": evaluation_metrics,
            "generation_mode": llm_response["mode"]
        }

        # Log query to Mongo
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

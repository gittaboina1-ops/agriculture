import os
import pandas as pd
import json
import logging
from typing import Dict, Any, List, Optional
from backend.config import settings

logger = logging.getLogger("graph_service")

class KnowledgeGraphService:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.driver = None
        self.connected_to_neo4j = False
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self._init_neo4j()
        self._build_in_memory_graph()

    def _init_neo4j(self):
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # Verify connectivity
            with self.driver.session() as session:
                session.run("RETURN 1 AS test")
            self.connected_to_neo4j = True
            logger.info("Successfully connected to live Neo4j instance.")
        except Exception as e:
            self.connected_to_neo4j = False
            logger.info(f"Neo4j live instance unavailable ({e}). Using full in-memory resilient graph engine.")

    def _add_node(self, node_id: str, label: str, name: str, properties: Dict[str, Any] = None):
        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            "name": name,
            "properties": properties or {}
        }

    def _add_edge(self, source_id: str, target_id: str, relationship: str, properties: Dict[str, Any] = None):
        self.edges.append({
            "source": source_id,
            "target": target_id,
            "relationship": relationship,
            "properties": properties or {}
        })

    def _build_in_memory_graph(self):
        self.nodes.clear()
        self.edges.clear()

        # 1. Crops
        crops_file = os.path.join(self.data_dir, "crops.csv")
        if os.path.exists(crops_file):
            df_crops = pd.read_csv(crops_file)
            for _, r in df_crops.iterrows():
                cid = str(r["crop_id"])
                self._add_node(cid, "Crop", r["common_name"], {
                    "scientific_name": r.get("scientific_name", ""),
                    "category": r.get("category", ""),
                    "optimal_temp": f"{r.get('optimal_temp_min')}-{r.get('optimal_temp_max')}°C",
                    "optimal_humidity": f"{r.get('optimal_humidity_min')}-{r.get('optimal_humidity_max')}%",
                    "description": r.get("description", "")
                })

        # 2. Diseases
        dis_file = os.path.join(self.data_dir, "diseases.csv")
        if os.path.exists(dis_file):
            df_dis = pd.read_csv(dis_file)
            for _, r in df_dis.iterrows():
                did = str(r["disease_id"])
                self._add_node(did, "Disease", r["name"], {
                    "pathogen_type": r.get("pathogen_type", ""),
                    "scientific_pathogen": r.get("scientific_pathogen", ""),
                    "symptoms": r.get("symptoms", ""),
                    "favorable_temp": f"{r.get('favorable_temp_min')}-{r.get('favorable_temp_max')}°C",
                    "favorable_humidity": f"{r.get('favorable_humidity_min')}-{r.get('favorable_humidity_max')}%",
                    "description": r.get("description", "")
                })

        # 3. Treatments
        trt_file = os.path.join(self.data_dir, "treatments.csv")
        if os.path.exists(trt_file):
            df_trt = pd.read_csv(trt_file)
            for _, r in df_trt.iterrows():
                tid = str(r["treatment_id"])
                self._add_node(tid, "Treatment", r["name"], {
                    "treatment_type": r.get("treatment_type", ""),
                    "active_agent": r.get("active_agent", ""),
                    "application_method": r.get("application_method", ""),
                    "description": r.get("description", "")
                })

        # 4. Weather Conditions
        wth_file = os.path.join(self.data_dir, "weather.csv")
        if os.path.exists(wth_file):
            df_wth = pd.read_csv(wth_file)
            for _, r in df_wth.iterrows():
                wid = str(r["condition_id"])
                self._add_node(wid, "WeatherCondition", r["name"], {
                    "temperature_avg": f"{r.get('temperature_avg')}°C",
                    "humidity_avg": f"{r.get('humidity_avg')}%",
                    "risk_factor": r.get("risk_factor", ""),
                    "description": r.get("description", "")
                })

        # 5. Soil
        soil_file = os.path.join(self.data_dir, "soil.csv")
        if os.path.exists(soil_file):
            df_soil = pd.read_csv(soil_file)
            for _, r in df_soil.iterrows():
                sid = str(r["soil_id"])
                self._add_node(sid, "Soil", r["soil_type"], {
                    "ph_range": f"{r.get('ph_min')}-{r.get('ph_max')}",
                    "drainage": r.get("drainage", ""),
                    "organic_matter": r.get("organic_matter", "")
                })

        # 6. Sources
        sources_file = os.path.join(self.data_dir, "sources.csv")
        if os.path.exists(sources_file):
            df_src = pd.read_csv(sources_file)
            for _, r in df_src.iterrows():
                sid = str(r["source_id"])
                self._add_node(sid, "Source", r["title"], {
                    "source_type": r.get("source_type", ""),
                    "confidence_score": float(r.get("confidence_score", 0.9)),
                    "publication_year": int(r.get("publication_year", 2024)),
                    "authors": r.get("authors_or_publisher", "")
                })

        # 7. Claims
        claims_file = os.path.join(self.data_dir, "claims.csv")
        if os.path.exists(claims_file):
            df_clm = pd.read_csv(claims_file)
            for _, r in df_clm.iterrows():
                cid = str(r["claim_id"])
                self._add_node(cid, "Claim", r["claim_text"][:40] + "...", {
                    "full_text": r.get("claim_text", ""),
                    "claim_type": r.get("claim_type", ""),
                    "status": r.get("status", "VERIFIED"),
                    "confidence": float(r.get("confidence", 0.8))
                })

        # 8. Observations
        obs_file = os.path.join(self.data_dir, "observations.json")
        if os.path.exists(obs_file):
            with open(obs_file, "r") as f:
                obs_data = json.load(f)
                for o in obs_data:
                    oid = o["observation_id"]
                    self._add_node(oid, "Observation", f"Obs: {o.get('crop_name')} ({o.get('suspected_disease')})", {
                        "farmer": o.get("farmer_name", ""),
                        "date": o.get("observed_date", ""),
                        "severity": o.get("severity", ""),
                        "symptoms": o.get("symptoms_reported", "")
                    })

        # 9. Sensors (Only VALID readings to preserve graph purity)
        sensors_file = os.path.join(self.data_dir, "sensors.json")
        if os.path.exists(sensors_file):
            with open(sensors_file, "r") as f:
                sens_data = json.load(f)
                for s in sens_data:
                    if s.get("status") == "VALID":
                        sid = s["sensor_id"]
                        if sid not in self.nodes:
                            self._add_node(sid, "Sensor", f"Station {sid}", {
                                "type": s.get("sensor_type", ""),
                                "field_id": s.get("field_id", "")
                            })

        # Establish Explicit Knowledge Relationships
        # (Crop)-[:SUSCEPTIBLE_TO]->(Disease)
        self._add_edge("CROP_001", "DIS_001", "SUSCEPTIBLE_TO", {"provenance": "DOC_001", "risk_level": "High"})
        self._add_edge("CROP_001", "DIS_002", "SUSCEPTIBLE_TO", {"provenance": "DOC_001", "risk_level": "High"})
        self._add_edge("CROP_001", "DIS_005", "SUSCEPTIBLE_TO", {"risk_level": "Moderate"})
        self._add_edge("CROP_002", "DIS_001", "SUSCEPTIBLE_TO", {"risk_level": "High"})
        self._add_edge("CROP_002", "DIS_002", "SUSCEPTIBLE_TO", {"risk_level": "Severe"})
        self._add_edge("CROP_003", "DIS_004", "SUSCEPTIBLE_TO", {"risk_level": "Moderate"})

        # (Disease)-[:TREATED_BY]->(Treatment)
        self._add_edge("DIS_001", "TRT_001", "TREATED_BY", {"efficacy": "88% preventative", "provenance": "DOC_001"})
        self._add_edge("DIS_001", "TRT_002", "TREATED_BY", {"efficacy": "85% protectant", "provenance": "DOC_001"})
        self._add_edge("DIS_001", "TRT_003", "TREATED_BY", {"efficacy": "78% biological", "provenance": "DOC_002"})
        self._add_edge("DIS_001", "TRT_005", "TREATED_BY", {"efficacy": "Disputed / Ineffective as curative", "provenance": "DOC_003 vs DOC_004", "conflict": True})

        # (Disease)-[:ASSOCIATED_WITH]->(WeatherCondition)
        self._add_edge("DIS_001", "WTH_001", "ASSOCIATED_WITH", {"trigger_humidity": ">80%", "trigger_temp": "24-30°C", "provenance": "DOC_001"})
        self._add_edge("DIS_002", "WTH_002", "ASSOCIATED_WITH", {"trigger_humidity": ">90%", "trigger_temp": "15-22°C"})

        # (Crop)-[:SUITABLE_FOR]->(Soil)
        self._add_edge("CROP_001", "SOIL_001", "SUITABLE_FOR", {"drainage_requirement": "Good"})
        self._add_edge("CROP_001", "SOIL_004", "SUITABLE_FOR", {"drainage_requirement": "High fertility"})

        # (Claim)-[:SUPPORTED_BY]->(Source)
        self._add_edge("CLM_001", "DOC_001", "SUPPORTED_BY", {"confidence": 0.95})
        self._add_edge("CLM_001", "DOC_007", "SUPPORTED_BY", {"confidence": 0.85})
        self._add_edge("CLM_002", "DOC_001", "SUPPORTED_BY", {"confidence": 0.88})
        self._add_edge("CLM_003", "DOC_002", "SUPPORTED_BY", {"confidence": 0.92})
        self._add_edge("CLM_004", "DOC_003", "SUPPORTED_BY", {"confidence": 0.65})
        self._add_edge("CLM_004", "DOC_004", "CONTRADICTED_BY", {"confidence": 0.94, "finding": "Neem Oil insufficient under high humidity"})
        self._add_edge("CLM_005", "DOC_001", "SUPPORTED_BY", {"confidence": 0.96})

        # (Observation)-[:OBSERVED_ON]->(Crop)
        self._add_edge("OBS_001", "CROP_001", "OBSERVED_ON", {"field": "Plot 4A"})
        self._add_edge("OBS_001", "DIS_001", "INDICATES_DISEASE", {"severity": "Moderate"})
        self._add_edge("OBS_002", "CROP_002", "OBSERVED_ON", {"field": "Plot 1B"})

        # (Sensor)-[:GENERATED]->(Observation / Telemetry)
        self._add_edge("SENSOR_WEATHER_TH_01", "WTH_001", "REPORTS_CONDITION", {"reading": "88.5% RH, 26.2°C", "provenance": "DOC_006"})

    def get_full_graph(self) -> Dict[str, Any]:
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "connected_to_neo4j": self.connected_to_neo4j,
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges)
        }

    def get_subgraph_for_entities(self, entity_ids: List[str], depth: int = 1) -> Dict[str, Any]:
        matched_node_ids = set(entity_ids)
        sub_edges = []

        # Find connected edges
        for edge in self.edges:
            if edge["source"] in matched_node_ids or edge["target"] in matched_node_ids:
                sub_edges.append(edge)
                matched_node_ids.add(edge["source"])
                matched_node_ids.add(edge["target"])

        sub_nodes = [self.nodes[nid] for nid in matched_node_ids if nid in self.nodes]

        return {
            "nodes": sub_nodes,
            "edges": sub_edges
        }

graph_service = KnowledgeGraphService()

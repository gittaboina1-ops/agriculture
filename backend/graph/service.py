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
        self.neo4j_error_reason: Optional[str] = None
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
            self.neo4j_error_reason = None
            logger.info("Successfully connected to live Neo4j instance.")
        except Exception as e:
            self.connected_to_neo4j = False
            self.neo4j_error_reason = str(e)
            logger.info(f"Neo4j live instance unavailable ({e}). Using full in-memory resilient graph engine.")

    def sync_to_neo4j(self):
        """Seeds or updates all in-memory nodes and edges into the live Neo4j instance."""
        if not self.connected_to_neo4j or not self.driver:
            return
        try:
            with self.driver.session() as session:
                # Sync nodes
                for n in self.nodes.values():
                    label = n.get("label", "Entity")
                    props = n.get("properties", {})
                    session.run(
                        f"""
                        MERGE (n:{label} {{id: $id}})
                        SET n.name = $name, n.provenance = $prov
                        """,
                        id=n["id"],
                        name=n["name"],
                        prov=props.get("provenance", "")
                    )
                # Sync edges
                for e in self.edges:
                    s_id = e["source"]
                    t_id = e["target"]
                    rel = e["relationship"]
                    props = e.get("properties", {})
                    session.run(
                        f"""
                        MATCH (s {{id: $s_id}}), (t {{id: $t_id}})
                        MERGE (s)-[r:{rel}]->(t)
                        SET r.provenance = $prov
                        """,
                        s_id=s_id,
                        t_id=t_id,
                        prov=props.get("provenance", "")
                    )
            logger.info(f"Synchronized {len(self.nodes)} nodes and {len(self.edges)} edges to live Neo4j.")
        except Exception as e:
            logger.warning(f"Failed to sync graph to Neo4j: {e}")

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

        # Synchronize base ontology to live Neo4j if connected
        if self.connected_to_neo4j:
            self.sync_to_neo4j()

    def get_live_neo4j_counts(self) -> Dict[str, int]:
        """Queries the live Neo4j database directly for node and edge counts."""
        if not self.connected_to_neo4j or not self.driver:
            return {"nodes": 0, "edges": 0}
        try:
            with self.driver.session() as session:
                n_res = session.run("MATCH (n) RETURN count(n) AS cnt").single()
                r_res = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()
                return {
                    "nodes": n_res["cnt"] if n_res else 0,
                    "edges": r_res["cnt"] if r_res else 0
                }
        except Exception as e:
            logger.warning(f"Error querying live Neo4j counts: {e}")
            return {"nodes": 0, "edges": 0}

    def query_live_neo4j(self, cypher: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Executes a Cypher query directly against the live Neo4j database."""
        if not self.connected_to_neo4j or not self.driver:
            return []
        try:
            with self.driver.session() as session:
                res = session.run(cypher, parameters or {})
                return [record.data() for record in res]
        except Exception as e:
            logger.warning(f"Cypher query error: {e}")
            return []

    def get_full_graph(self) -> Dict[str, Any]:
        live_counts = self.get_live_neo4j_counts() if self.connected_to_neo4j else {}
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "connected_to_neo4j": self.connected_to_neo4j,
            "total_nodes": live_counts.get("nodes", len(self.nodes)),
            "total_edges": live_counts.get("edges", len(self.edges)),
            "in_memory_nodes": len(self.nodes),
            "in_memory_edges": len(self.edges),
            "live_neo4j_nodes": live_counts.get("nodes", 0),
            "live_neo4j_edges": live_counts.get("edges", 0)
        }

    def get_subgraph_for_entities(self, entity_ids: List[str], depth: int = 1) -> Dict[str, Any]:
        # If live Neo4j is connected, query live Neo4j directly
        if self.connected_to_neo4j and self.driver:
            try:
                cypher = """
                MATCH (s)-[r]->(t)
                WHERE s.id IN $eids OR t.id IN $eids
                RETURN s.id AS s_id, labels(s)[0] AS s_label, s.name AS s_name,
                       type(r) AS rel, properties(r) AS r_props,
                       t.id AS t_id, labels(t)[0] AS t_label, t.name AS t_name
                """
                records = self.query_live_neo4j(cypher, {"eids": entity_ids})
                if records:
                    sub_nodes = {}
                    sub_edges = []
                    for rec in records:
                        s_id = rec["s_id"]
                        t_id = rec["t_id"]
                        if s_id not in sub_nodes:
                            sub_nodes[s_id] = {"id": s_id, "label": rec["s_label"], "name": rec["s_name"]}
                        if t_id not in sub_nodes:
                            sub_nodes[t_id] = {"id": t_id, "label": rec["t_label"], "name": rec["t_name"]}
                        sub_edges.append({
                            "source": s_id,
                            "target": t_id,
                            "relationship": rec["rel"],
                            "properties": rec["r_props"]
                        })
                    return {
                        "nodes": list(sub_nodes.values()),
                        "edges": sub_edges
                    }
            except Exception as e:
                logger.warning(f"Neo4j subgraph traversal failed: {e}. Falling back to in-memory.")

        # In-memory fallback
        matched_node_ids = set(entity_ids)
        sub_edges = []
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

import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.models.schemas import FarmerQueryRequest, FarmerQueryResponse, GraphData
from backend.graph.service import graph_service
from backend.provenance.tracker import provenance_tracker
from backend.conflict.engine import conflict_engine
from backend.validation.validator import validation_service
from backend.retrieval.service import retrieval_service
from backend.services.mongo_service import mongo_service

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AgriGraph: Dynamic Agricultural Knowledge Graph with Source Provenance, Conflict Detection & Sensor Validation"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AgriGraph API",
        "neo4j_live": graph_service.connected_to_neo4j,
        "mongo_live": mongo_service.connected,
        "mode": "resilient_hybrid",
        "version": settings.VERSION
    }

@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    full_graph = graph_service.get_full_graph()
    sources = provenance_tracker.get_all_sources()
    conflicts = conflict_engine.evaluate_claims(provenance_tracker.claims, provenance_tracker.sources)
    coverage = provenance_tracker.get_provenance_coverage()

    sensors_file = os.path.join("data", "sensors.json")
    val_res = {"invalid_count": 3, "total_processed": 7}
    if os.path.exists(sensors_file):
        with open(sensors_file, "r") as f:
            raw_sensors = json.load(f)
            val_res = validation_service.process_readings(raw_sensors)

    crops_count = sum(1 for n in full_graph["nodes"] if n["label"] == "Crop")
    diseases_count = sum(1 for n in full_graph["nodes"] if n["label"] == "Disease")
    treatments_count = sum(1 for n in full_graph["nodes"] if n["label"] == "Treatment")

    return {
        "total_crops": crops_count,
        "total_diseases": diseases_count,
        "total_treatments": treatments_count,
        "total_sources": len(sources),
        "total_relationships": len(full_graph["edges"]),
        "total_nodes": len(full_graph["nodes"]),
        "conflicts_detected": len(conflicts),
        "invalid_sensor_records": val_res["invalid_count"],
        "provenance_coverage": coverage,
        "neo4j_connected": graph_service.connected_to_neo4j,
        "mongodb_connected": mongo_service.connected
    }

@app.post("/api/query", response_model=FarmerQueryResponse)
def execute_query(req: FarmerQueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")
    return retrieval_service.execute_farmer_query(req.query)

@app.get("/api/graph")
def get_graph():
    return graph_service.get_full_graph()

@app.get("/api/sources")
def get_sources():
    return {
        "sources": provenance_tracker.get_all_sources(),
        "coverage": provenance_tracker.get_provenance_coverage()
    }

@app.get("/api/conflicts")
def get_conflicts():
    conflicts = conflict_engine.evaluate_claims(provenance_tracker.claims, provenance_tracker.sources)
    unverified = conflict_engine.find_unverified_claims(provenance_tracker.claims, provenance_tracker.sources)
    return {
        "conflicts": conflicts,
        "unverified_claims": unverified,
        "total_conflicts": len(conflicts)
    }

@app.get("/api/validation")
def get_validation_report():
    sensors_file = os.path.join("data", "sensors.json")
    if os.path.exists(sensors_file):
        with open(sensors_file, "r") as f:
            raw_sensors = json.load(f)
            return validation_service.process_readings(raw_sensors)
    return {"error": "Sensors dataset file not found"}

@app.get("/api/crops")
def get_crops():
    return [n for n in graph_service.nodes.values() if n["label"] == "Crop"]

@app.get("/api/diseases")
def get_diseases():
    return [n for n in graph_service.nodes.values() if n["label"] == "Disease"]

@app.get("/api/history")
def get_history():
    return mongo_service.get_query_history()

@app.get("/api/farmers")
def get_farmers():
    return mongo_service.get_farmer_profiles()

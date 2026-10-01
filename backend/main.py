import json
import os
import time
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.models.schemas import FarmerQueryRequest, FarmerQueryResponse, GraphData
from backend.graph.service import graph_service
from backend.provenance.tracker import provenance_tracker
from backend.conflict.engine import conflict_engine
from backend.validation.validator import validation_service
from backend.retrieval.service import retrieval_service
from backend.services.mongo_service import mongo_service
from backend.services.auth_service import auth_service

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AgriGraph: Dynamic Agricultural Knowledge Graph with Source Provenance, Conflict Detection & Sensor Validation"
)

# Environment-aware CORS configuration for local development & production deployment (Render)
cors_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

frontend_url = os.getenv("FRONTEND_URL") or os.getenv("CLIENT_URL")
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")

if frontend_url:
    for url in frontend_url.split(","):
        cleaned = url.strip().rstrip("/")
        if cleaned and cleaned not in cors_origins:
            cors_origins.append(cleaned)

if allowed_origins_env:
    for url in allowed_origins_env.split(","):
        cleaned = url.strip().rstrip("/")
        if cleaned and cleaned not in cors_origins:
            cors_origins.append(cleaned)

if "*" not in cors_origins and not frontend_url and not allowed_origins_env:
    cors_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    neo4j_status = "CONNECTED" if graph_service.connected_to_neo4j else "FALLBACK"
    mongo_status = "CONNECTED" if mongo_service.connected else "FALLBACK"
    semantic_status = "LOADED" if retrieval_service.model_status == "loaded" else "FALLBACK"
    llm_status = "AVAILABLE" if (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")) else "FALLBACK"

    live_neo4j_stats = graph_service.get_live_neo4j_counts() if graph_service.connected_to_neo4j else {"nodes": 0, "edges": 0}

    return {
        "status": "healthy",
        "service": "AgriGraph API",
        "version": settings.VERSION,
        "mode": "resilient_hybrid",
        "neo4j": neo4j_status,
        "mongodb": mongo_status,
        "semantic_model": semantic_status,
        "llm": llm_status,
        "components": {
            "neo4j": {
                "status": neo4j_status,
                "connected": graph_service.connected_to_neo4j,
                "uri": settings.NEO4J_URI,
                "live_nodes": live_neo4j_stats["nodes"],
                "live_edges": live_neo4j_stats["edges"],
                "diagnostic": graph_service.neo4j_error_reason or f"Connected to live Neo4j instance at {settings.NEO4J_URI}"
            },
            "mongodb": {
                "status": mongo_status,
                "connected": mongo_service.connected,
                "uri": settings.MONGODB_URI,
                "diagnostic": mongo_service.mongo_error_reason or "Connected to live MongoDB instance"
            },
            "semantic_model": {
                "status": semantic_status,
                "model_name": settings.EMBEDDING_MODEL_NAME
            },
            "llm": {
                "status": llm_status,
                "mode": "external_api" if llm_status == "AVAILABLE" else "grounded_rule_engine"
            },
            "knowledge_graph": {
                "in_memory_nodes": len(graph_service.nodes),
                "in_memory_edges": len(graph_service.edges),
                "live_neo4j_nodes": live_neo4j_stats["nodes"],
                "live_neo4j_edges": live_neo4j_stats["edges"]
            },
            "provenance": {
                "sources_tracked": len(provenance_tracker.sources),
                "claims_tracked": len(provenance_tracker.claims)
            }
        },
        "neo4j_live": graph_service.connected_to_neo4j,
        "mongo_live": mongo_service.connected
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

def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """Allows authenticated queries, falls back to demo farmer if called directly from CLI / demo runner."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = auth_service.verify_jwt_token(token)
        if payload:
            return payload
    return None

@app.post("/api/query", response_model=FarmerQueryResponse)
def execute_query(req: FarmerQueryRequest, authorization: Optional[str] = Header(None)):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")
    # Verify user token if provided or allow demo execution
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        if not auth_service.verify_jwt_token(token):
            raise HTTPException(status_code=401, detail="Invalid or expired session token.")
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

# ============================================================
# Authentication, RBAC & User Management APIs
# ============================================================
from fastapi import Header, Depends, UploadFile, File, Form
from backend.services.auth_service import auth_service
from backend.services.translation_service import translation_service
from backend.models.schemas import (
    SignupRequest, LoginRequest, AuthResponse, UserInfo,
    TranslationRequest, TranslationResponse
)
from backend.ingestion.document_service import document_service

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Dependency: validates JWT Bearer token and returns user payload."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required. Please log in.")
    token = authorization.split(" ")[1]
    payload = auth_service.verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired session token. Please log in again.")
    return payload

def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency: ensures user has admin role."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required. Access forbidden.")
    return user

@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(req: SignupRequest):
    name = req.name.strip()
    email = req.email.strip().lower()
    role = (req.role or "farmer").strip().lower()

    if not name or not email or not req.password:
        raise HTTPException(status_code=400, detail="Name, email, and password are required.")

    if req.confirm_password and req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

    # AgriGraph public signup is strictly for farmers. Admin accounts cannot be created via public signup.
    if role != "farmer":
        # Only allow admin creation if matching admin secret code is explicitly provided
        if role == "admin" and req.admin_code and req.admin_code.strip() == settings.ADMIN_SIGNUP_CODE:
            role = "admin"
        else:
            raise HTTPException(status_code=403, detail="Public registration is restricted to Farmer accounts.")

    try:
        user_record = auth_service.create_user(name=name, email=email, password=req.password, role=role)
        token = auth_service.create_jwt_token(user_record)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user_record["id"],
                "name": user_record["name"],
                "email": user_record["email"],
                "role": user_record["role"]
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login", response_model=AuthResponse)
def login(req: LoginRequest):
    email = req.email.strip().lower()
    user = auth_service.get_user_by_email(email)
    if not user or not auth_service.verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = auth_service.create_jwt_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@app.get("/api/auth/me")
def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "id": user.get("sub"),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role")
    }

# ============================================================
# Translation API
# ============================================================
@app.post("/api/translate", response_model=TranslationResponse)
def translate_answer(req: TranslationRequest):
    target_lang = req.target_language.strip().capitalize() if req.target_language else "Telugu"
    
    # 1. If structured result provided, translate complete result
    if req.result:
        translated_result = translation_service.translate_structured_result(req.result, target_lang)
        return {
            "target_language": target_lang,
            "translated_result": translated_result,
            "translated_text": translated_result.get("agricultural_insight", "")
        }

    # 2. Text translation fallback
    if req.text and req.text.strip():
        res = translation_service.translate_text(req.text, target_lang)
        return {
            "target_language": target_lang,
            "translated_text": res["translated_text"],
            "translated_result": None
        }

    return {
        "target_language": target_lang,
        "translated_text": "",
        "translated_result": None
    }

# ============================================================
# Admin Document Ingestion & Knowledge Graph Construction APIs
# ============================================================
from backend.models.schemas import UploadResourceRequest

@app.post("/api/admin/upload")
def upload_research_document(
    req: UploadResourceRequest,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Accepts PDF, CSV, or JSON agricultural resources via JSON payload (with base64 file content).
    Saves document and optionally processes it into knowledge graph.
    """
    filename = req.filename or "uploaded_resource.pdf"
    file_ext = filename.lower().split(".")[-1]
    if file_ext not in ["pdf", "csv", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, CSV, or JSON.")

    try:
        raw_b64 = req.file_content_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        import base64
        file_bytes = base64.b64decode(raw_b64)
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file payload: {str(e)}")

    file_path = os.path.join(document_service.upload_dir, f"{int(time.time())}_{filename}")
    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    doc_type = "Dataset" if file_ext in ["csv", "json"] else (req.source_type or "Research Paper")
    doc_entry = document_service.register_document(
        file_path=file_path,
        filename=filename,
        title=req.title,
        source_type=doc_type,
        authors=req.authors or "Unknown Author",
        publication_year=req.publication_year or 2026,
        confidence_score=req.confidence_score or 0.92
    )

    if req.process_immediately:
        try:
            res = document_service.process_document(doc_entry["document_id"])
            return {
                "status": "COMPLETED",
                "document_id": doc_entry["document_id"],
                "filename": filename,
                "title": doc_entry["title"],
                "stats": res["stats"],
                "conflicts": res["conflicts"],
                "message": "Resource successfully ingested and Knowledge Graph updated."
            }
        except Exception as e:
            return {
                "status": "FAILED",
                "document_id": doc_entry["document_id"],
                "error": str(e),
                "message": f"Processing failed: {str(e)}"
            }

    return {
        "status": "UPLOADED",
        "document_id": doc_entry["document_id"],
        "filename": filename,
        "title": doc_entry["title"],
        "message": "Resource uploaded. Click 'Create Knowledge Graph' to begin extraction."
    }

@app.post("/api/admin/documents/{document_id}/create-graph")
def trigger_create_knowledge_graph(
    document_id: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Admin explicit trigger to process an uploaded document and update Knowledge Graph."""
    doc = document_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")

    if doc.get("status") == "COMPLETED":
        return {
            "status": "COMPLETED",
            "document_id": document_id,
            "stats": doc.get("stats", {}),
            "message": "Knowledge Graph already contains this document's verified nodes and relationships."
        }

    try:
        res = document_service.process_document(document_id)
        return {
            "status": "COMPLETED",
            "document_id": document_id,
            "stats": res["stats"],
            "conflicts": res["conflicts"],
            "message": "Knowledge Graph construction completed successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph construction failed: {str(e)}")

@app.get("/api/admin/documents")
def list_admin_documents(current_user: Dict[str, Any] = Depends(require_admin)):
    return document_service.list_documents()

@app.get("/api/admin/documents/{document_id}")
def get_admin_document_details(document_id: str, current_user: Dict[str, Any] = Depends(require_admin)):
    doc = document_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")
    return doc

@app.get("/api/admin/documents/{document_id}/status")
def get_admin_document_status(document_id: str):
    doc = document_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")
    return {
        "document_id": document_id,
        "status": doc.get("status"),
        "stats": doc.get("stats", {}),
        "error": doc.get("error")
    }



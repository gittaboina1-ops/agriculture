from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SensorReading(BaseModel):
    reading_id: str
    sensor_id: str
    sensor_type: str
    timestamp: str
    field_id: str
    metric: str
    value: float
    unit: str
    status: str = "VALID"
    anomaly_reason: Optional[str] = None
    action_taken: Optional[str] = None

class ValidationResult(BaseModel):
    is_valid: bool
    reading_id: str
    sensor_id: str
    metric: str
    value: float
    reason: Optional[str] = None
    action: Optional[str] = None

class FarmerObservation(BaseModel):
    observation_id: str
    farmer_id: str
    farmer_name: str
    crop_id: str
    crop_name: str
    field_name: str
    observed_date: str
    symptoms_reported: str
    suspected_disease: str
    severity: str
    source_id: str
    verified_by_agronomist: bool = True

class SourceInfo(BaseModel):
    source_id: str
    title: str
    source_type: str
    authors_or_publisher: str
    publication_year: int
    confidence_score: float
    summary: str
    is_synthetic: bool = False

class ConflictRecord(BaseModel):
    claim_id: str
    entity_name: str
    claim_text: str
    supporting_sources: List[Dict[str, Any]]
    contradicting_sources: List[Dict[str, Any]]
    status: str = "CONFLICTING"
    notes: Optional[str] = None

class GraphNode(BaseModel):
    id: str
    label: str
    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class FarmerQueryRequest(BaseModel):
    query: str
    crop: Optional[str] = None
    farm_id: Optional[str] = None

class FarmerQueryResponse(BaseModel):
    query: str
    matched_crop: Optional[str] = None
    matched_disease: Optional[str] = None
    agricultural_insight: str
    relevant_factors: List[str]
    evidence: List[Dict[str, Any]]
    sources: List[SourceInfo]
    conflicts: List[ConflictRecord]
    data_quality_warnings: List[Dict[str, Any]]
    subgraph: GraphData
    evaluation_metrics: Dict[str, Any]
    generation_mode: Optional[str] = "grounded_rule_engine"
    provider: Optional[str] = "fallback"
    model: Optional[str] = None
    fallback_reason: Optional[str] = None

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: Optional[str] = None
    role: Optional[str] = "farmer"
    admin_code: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class UserInfo(BaseModel):
    id: str
    name: str
    email: str
    role: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo

class TranslationRequest(BaseModel):
    text: Optional[str] = None
    target_language: str = "Telugu"
    result: Optional[Dict[str, Any]] = None

class TranslationResponse(BaseModel):
    translated_text: Optional[str] = None
    target_language: str
    translated_result: Optional[Dict[str, Any]] = None

class UploadResourceRequest(BaseModel):
    filename: str
    file_content_base64: str
    title: Optional[str] = None
    source_type: Optional[str] = "Research Paper"
    authors: Optional[str] = "Unknown Author"
    publication_year: Optional[int] = 2026
    confidence_score: Optional[float] = 0.92
    process_immediately: Optional[bool] = True



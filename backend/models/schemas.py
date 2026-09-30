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

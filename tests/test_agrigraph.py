from fastapi.testclient import TestClient
from backend.main import app
from backend.validation.validator import validation_service
from backend.conflict.engine import conflict_engine

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "AgriGraph" in data["service"]

def test_dashboard_stats():
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_crops"] >= 5
    assert data["total_diseases"] >= 5
    assert data["conflicts_detected"] >= 1
    assert data["invalid_sensor_records"] >= 1
    assert data["provenance_coverage"]["coverage_percentage"] > 70.0

def test_farmer_query_core_scenario():
    query = "Why is my tomato crop at high disease risk and what evidence supports this?"
    res = client.post("/api/query", json={"query": query})
    assert res.status_code == 200
    data = res.json()
    assert data["matched_crop"] == "Tomato"
    assert data["matched_disease"] == "Early Blight"
    assert len(data["relevant_factors"]) > 0
    assert len(data["evidence"]) > 0
    assert len(data["sources"]) > 0
    assert len(data["conflicts"]) >= 1
    assert len(data["data_quality_warnings"]) >= 1
    assert data["subgraph"]["nodes"]

def test_sensor_validation_logic():
    # Corrupted temperature (250 C)
    bad_temp = {"sensor_id": "SN_BAD_01", "metric": "temperature", "value": 250.0}
    is_valid, reason, action = validation_service.validate_reading(bad_temp)
    assert not is_valid
    assert "outside valid physical range" in reason

    # Corrupted negative humidity
    bad_hum = {"sensor_id": "SN_BAD_02", "metric": "humidity", "value": -20.0}
    is_valid, reason, action = validation_service.validate_reading(bad_hum)
    assert not is_valid

    # Valid ambient reading
    good_temp = {"sensor_id": "SN_GOOD_01", "metric": "temperature", "value": 25.5}
    is_valid, reason, action = validation_service.validate_reading(good_temp)
    assert is_valid

def test_conflict_detection_logic():
    claims = [{
        "claim_id": "CLM_TEST",
        "entity_name": "Neem Oil Extract",
        "claim_text": "Neem oil is curative",
        "status": "CONFLICTING",
        "supporting_source_ids": "DOC_003",
        "contradicting_source_ids": "DOC_004"
    }]
    sources_map = {
        "DOC_003": {"source_id": "DOC_003", "title": "Doc 3"},
        "DOC_004": {"source_id": "DOC_004", "title": "Doc 4"}
    }
    conflicts = conflict_engine.evaluate_claims(claims, sources_map)
    assert len(conflicts) == 1
    assert len(conflicts[0]["supporting_sources"]) == 1
    assert len(conflicts[0]["contradicting_sources"]) == 1

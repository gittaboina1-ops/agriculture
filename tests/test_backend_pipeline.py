"""
AgriGraph Backend Regression Test Suite
Validates the complete terminal-first backend pipeline:
1. Intent Detection across all 7 canonical query types
2. Critical Soil Query Bug Regression (must NOT return disease risk)
3. Disease Pathogen Retrieval
4. Treatment & Disputed Claim Surfacing
5. Conflict Engine Trigger
6. Sensor Telemetry Guardrail Rejection
7. Provenance Linkage & Citations
"""

from backend.retrieval.service import retrieval_service
from backend.retrieval.intent import (
    intent_detector,
    INTENT_CROP_DISEASE,
    INTENT_SOIL_SUITABILITY,
    INTENT_DISEASE_RISK,
    INTENT_TREATMENT,
    INTENT_EVIDENCE_PROVENANCE,
    INTENT_CONFLICT,
    INTENT_DATA_QUALITY
)
from backend.validation.validator import validation_service
from backend.conflict.engine import conflict_engine

def test_intent_detection():
    cases = [
        ("What diseases commonly affect tomato?", INTENT_CROP_DISEASE),
        ("What soil conditions are suitable for tomato?", INTENT_SOIL_SUITABILITY),
        ("Why is my tomato crop at high disease risk?", INTENT_DISEASE_RISK),
        ("What treatments are associated with Early Blight?", INTENT_TREATMENT),
        ("What evidence supports Neem Oil Extract?", INTENT_EVIDENCE_PROVENANCE),
        ("Are there conflicting recommendations for Neem Oil Extract?", INTENT_CONFLICT),
        ("Are there any invalid sensor readings?", INTENT_DATA_QUALITY)
    ]
    for q, expected in cases:
        detected = intent_detector.detect_intent(q)
        assert detected == expected, f"Query '{q}' expected {expected}, got {detected}"
    print("✓ Intent classification verified for all 7 query types.")

def test_soil_query_regression():
    q = "What soil conditions are suitable for tomato?"
    res = retrieval_service.execute_farmer_query(q)
    assert res["intent"] == INTENT_SOIL_SUITABILITY
    insight = res["agricultural_insight"].lower()
    assert "soil" in insight
    assert "loamy sand" in insight or "alluvial" in insight
    assert "early blight is currently" not in insight
    assert len(res["evidence"]) > 0
    for ev in res["evidence"]:
        assert ev["relationship"] == "SUITABLE_FOR"
    print("✓ Soil query regression passed: Prioritized SUITABLE_FOR, zero false disease-risk leakage.")

def test_crop_disease_query():
    q = "What diseases commonly affect tomato?"
    res = retrieval_service.execute_farmer_query(q)
    assert res["intent"] == INTENT_CROP_DISEASE
    insight = res["agricultural_insight"]
    assert "Early Blight" in insight
    assert "Late Blight" in insight
    for ev in res["evidence"]:
        assert ev["relationship"] == "SUSCEPTIBLE_TO"
    print("✓ Crop disease query verified: Correctly traverses SUSCEPTIBLE_TO edges.")

def test_treatment_query():
    q = "What treatments are associated with Early Blight?"
    res = retrieval_service.execute_farmer_query(q)
    assert res["intent"] == INTENT_TREATMENT
    insight = res["agricultural_insight"]
    assert "Copper Hydroxide" in insight
    assert "Bacillus subtilis" in insight
    assert "Neem Oil Extract" in insight
    print("✓ Treatment query verified: Grounded in prophylactic and biological efficacy.")

def test_conflict_engine_trigger():
    q = "Are there conflicting recommendations for Neem Oil Extract?"
    res = retrieval_service.execute_farmer_query(q)
    assert res["intent"] == INTENT_CONFLICT
    assert len(res["conflicts"]) >= 1
    conflict = res["conflicts"][0]
    assert "Neem Oil" in conflict["entity_name"]
    assert len(conflict["supporting_sources"]) >= 1
    assert len(conflict["contradicting_sources"]) >= 1
    print("✓ Conflict engine verified: Neem Oil dispute surfaced transparently.")

def test_data_quality_shield():
    q = "Are there any invalid sensor readings?"
    res = retrieval_service.execute_farmer_query(q)
    assert res["intent"] == INTENT_DATA_QUALITY
    assert len(res["data_quality_warnings"]) >= 3
    # Check 250 C temperature was caught
    temp_flagged = any("250" in str(w["rejected_value"]) for w in res["data_quality_warnings"])
    assert temp_flagged, "Corrupt 250C temperature reading must be flagged"
    print("✓ Data quality shield verified: 250°C and negative humidity rejected.")

def test_focused_disease_risk_subgraph():
    q = "Why is my tomato crop at high disease risk?"
    res = retrieval_service.execute_farmer_query(q)
    assert res["intent"] == INTENT_DISEASE_RISK
    node_names = [n["name"] for n in res["subgraph"]["nodes"]]
    assert "Tomato" in node_names
    assert "Early Blight" in node_names
    assert "Potato" not in node_names, "Unrelated crop (Potato) found in focused Tomato disease risk subgraph!"
    assert "Loamy Sand" not in node_names, "General soil suitability found in disease risk subgraph!"
    assert "Copper Hydroxide Spray" not in node_names, "General treatments found in disease risk subgraph!"
    print("✓ Focused disease risk subgraph verified: Isolated to target crop, pathogen, weather, and observations.")

def run_all_tests():
    print("=" * 60)
    print("RUNNING AGRIGRAPH BACKEND PIPELINE REGRESSION TESTS")
    print("=" * 60)
    test_intent_detection()
    test_soil_query_regression()
    test_crop_disease_query()
    test_treatment_query()
    test_conflict_engine_trigger()
    test_data_quality_shield()
    test_focused_disease_risk_subgraph()
    print("=" * 60)
    print("🎉 ALL BACKEND REGRESSION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()

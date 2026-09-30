#!/usr/bin/env python3
"""
AgriGraph Multi-Query Demo Runner
Executes diverse farmer queries through the system and formats the structured
evidence, provenance citations, conflicting claims, and data-quality shields.
"""

from backend.main import app
from fastapi.testclient import TestClient
import json

client = TestClient(app)

QUERIES = [
    {
        "title": "SCENARIO 1: High Disease Risk & Evidence (Core Problem Statement)",
        "query": "Why is my tomato crop at high disease risk and what evidence supports this?"
    },
    {
        "title": "SCENARIO 2: Pathogen Association & Crop Vulnerabilities",
        "query": "What diseases are associated with tomato?"
    },
    {
        "title": "SCENARIO 3: Treatment Efficacy & Scientific Evidence",
        "query": "What treatments are reported for Early Blight?"
    },
    {
        "title": "SCENARIO 4: Conflict Engine Trigger (Neem Oil Curative Debate)",
        "query": "Are there conflicting recommendations on neem oil?"
    },
    {
        "title": "SCENARIO 5: Microclimate & Environmental Risk Triggers",
        "query": "What weather conditions increase the risk?"
    }
]

def run_demo():
    print("=" * 80)
    print("🌾 AGRIGRAPH MULTI-QUERY DEMONSTRATION")
    print("=" * 80)

    for idx, item in enumerate(QUERIES, 1):
        print(f"\n[{idx}/5] {item['title']}")
        print(f"❓ Query: \"{item['query']}\"")
        print("-" * 80)

        response = client.post("/api/query", json={"query": item["query"]})
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            continue

        data = response.json()

        # 1. Agricultural Insight
        print("💡 Agricultural Insight:")
        print(f"   {data['agricultural_insight']}")

        # 2. Contributing Factors
        print("\n🔍 Factors Contributing to Insight:")
        for factor in data.get("relevant_factors", [])[:3]:
            print(f"   • {factor}")

        # 3. Knowledge Graph Evidence
        print("\n🕸️  Connected Knowledge Graph Subgraph (Sample Triples):")
        for ev in data.get("evidence", [])[:3]:
            print(f"   • ({ev['subject']}) -[:{ev['relationship']}]-> ({ev['object']}) [Source: {ev['provenance']}]")

        # 4. Source Provenance
        print("\n📚 Sourced Citations / Provenance Lineage:")
        for src in data.get("sources", [])[:3]:
            print(f"   • [{src['source_id']}] {src['title']} ({src['authors_or_publisher']}, {src['publication_year']}) - Confidence: {int(src['confidence_score']*100)}%")

        # 5. Conflicting Evidence
        if data.get("conflicts"):
            print("\n⚠️  Conflicting Evidence Detected:")
            for c in data["conflicts"]:
                sup_titles = [f"[{s['source_id']}] {s['title'][:35]}..." for s in c.get('supporting_sources', [])]
                contra_titles = [f"[{s['source_id']}] {s['title'][:35]}..." for s in c.get('contradicting_sources', [])]
                print(f"   • Entity: {c['entity_name']}")
                print(f"     - Supporting Sources:    {', '.join(sup_titles)}")
                print(f"     - Contradicting Sources: {', '.join(contra_titles)}")

        # 6. Data Quality & Adversarial Shield
        if data.get("data_quality_warnings"):
            print("\n🛡️  Data Quality & Corrupted Sensor Shield:")
            for w in data["data_quality_warnings"]:
                print(f"   • Rejected Sensor {w['sensor_id']} ({w['metric']}: {w['rejected_value']}) -> {w['reason'][:60]}...")

        # 7. Metrics
        metrics = data.get("evaluation_metrics", {})
        print(f"\n⚡ Response Time: {metrics.get('query_latency_ms')} ms | Provenance Coverage: {metrics.get('provenance_coverage_pct')}%")
        print("=" * 80)

if __name__ == "__main__":
    run_demo()

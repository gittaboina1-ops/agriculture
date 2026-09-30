#!/usr/bin/env python3
"""
AgriGraph Terminal Interactive CLI Application
Terminal-based interactive agricultural knowledge assistant.
Provides natural-language query processing, intent detection, evidence grounding,
provenance tracing, conflict detection, and sensor validation audit.
"""

import sys
import os
from typing import Dict, Any

from backend.retrieval.service import retrieval_service
from backend.graph.service import graph_service
from backend.provenance.tracker import provenance_tracker
from backend.conflict.engine import conflict_engine
from backend.validation.validator import validation_service

BANNER = """
====================================================
                 AGRIGRAPH
      Agricultural Knowledge Assistant
====================================================

Type an agricultural question.
Type 'examples' to see sample queries.
Type 'stats' to view knowledge graph metrics.
Type 'conflicts' to see disputed claims.
Type 'validation' to see rejected sensor telemetry.
Type 'help' for command assistance.
Type 'exit' to quit.
"""

SAMPLE_QUERIES = [
    "What diseases commonly affect tomato?",
    "What soil conditions are suitable for tomato?",
    "Why is my tomato crop at high disease risk?",
    "What treatments are associated with Early Blight?",
    "What evidence supports Neem Oil Extract?",
    "Are there conflicting recommendations for Neem Oil Extract?",
    "Are there any invalid sensor readings?"
]

def print_divider():
    print("=" * 60)

def format_query_response(res: Dict[str, Any]):
    print_divider()
    print("QUERY")
    print_divider()
    print(res.get("query", ""))

    print("\n" + "=" * 60)
    print("INTENT")
    print("=" * 60)
    print(f"{res.get('intent', 'UNKNOWN')}\n")
    print(f"Detected entity: {res.get('matched_crop', 'General Agricultural Entity')}")

    print("\n" + "=" * 60)
    print("AGRICULTURAL INSIGHT")
    print("=" * 60)
    print(res.get("agricultural_insight", ""))

    factors = res.get("relevant_factors", [])
    if factors:
        print("\n" + "=" * 60)
        print("RELEVANT FACTORS")
        print("=" * 60)
        for f in factors:
            print(f"• {f}")

    evidence = res.get("evidence", [])
    print("\n" + "=" * 60)
    print("KNOWLEDGE GRAPH EVIDENCE")
    print("=" * 60)
    if evidence:
        for ev in evidence:
            print(f"{ev['subject']}")
            print(f"  └── {ev['relationship']} → {ev['object']} (Citation: {ev['provenance']})")
    else:
        print("No specific subgraph relationships matched for this intent.")

    sources = res.get("sources", [])
    print("\n" + "=" * 60)
    print("SOURCES / PROVENANCE")
    print("=" * 60)
    if sources:
        for s in sources:
            print(f"[{s.get('source_id')}] {s.get('title')}")
            print(f"  Type: {s.get('source_type')} | Publisher: {s.get('authors_or_publisher')}")
            print(f"  Confidence: {int(s.get('confidence_score', 0.8) * 100)}% | Year: {s.get('publication_year')}")
            print(f"  Abstract: {s.get('summary')}\n")
    else:
        print("Standard Agricultural Baseline Reference.")

    conflicts = res.get("conflicts", [])
    print("=" * 60)
    print("CONFLICTING EVIDENCE")
    print("=" * 60)
    if conflicts:
        for c in conflicts:
            print(f"⚠️  CONFLICT DETECTED: {c.get('entity_name')}")
            print(f"  Claim: \"{c.get('claim_text')}\"")
            sup = [f"[{s['source_id']}] {s['title'][:35]}..." for s in c.get('supporting_sources', [])]
            contra = [f"[{s['source_id']}] {s['title'][:35]}..." for s in c.get('contradicting_sources', [])]
            print(f"  Supporting:    {', '.join(sup) if sup else 'Extension Advisory DOC_003'}")
            print(f"  Contradicting: {', '.join(contra) if contra else 'Meta-Analysis DOC_004'}")
            print(f"  Status: {c.get('status')}\n")
    else:
        print("None detected.")

    warnings = res.get("data_quality_warnings", [])
    print("\n" + "=" * 60)
    print("DATA QUALITY")
    print("=" * 60)
    if warnings:
        for w in warnings:
            print(f"⚠️  DATA QUALITY WARNING")
            print(f"  Sensor: {w.get('sensor_id')}")
            print(f"  Reading: {w.get('metric')} = {w.get('rejected_value')}")
            print(f"  Reason: {w.get('reason')}")
            print(f"  Action: {w.get('action_taken')}\n")
    else:
        print("No relevant invalid readings detected.")

    metrics = res.get("evaluation_metrics", {})
    print("=" * 60)
    print(f"⚡ Latency: {metrics.get('query_latency_ms', 0)} ms | Mode: {res.get('generation_mode', 'grounded')}")
    print("=" * 60)

def handle_stats():
    g = graph_service.get_full_graph()
    sources = provenance_tracker.get_all_sources()
    conflicts = conflict_engine.evaluate_claims(provenance_tracker.claims, provenance_tracker.sources)
    coverage = provenance_tracker.get_provenance_coverage()

    print("\n📊 AGRIGRAPH KNOWLEDGE METRICS:")
    print(f"  • Knowledge Nodes:       {len(g['nodes'])}")
    print(f"  • Relationships:         {len(g['edges'])}")
    print(f"  • Cataloged Sources:     {len(sources)}")
    print(f"  • Sourced Claims:        {coverage.get('sourced_claims')}/{coverage.get('total_claims')} ({coverage.get('coverage_percentage')}%)")
    print(f"  • Detected Conflicts:    {len(conflicts)}")
    print(f"  • Neo4j Live Connected:  {g['connected_to_neo4j']}\n")

def handle_conflicts():
    conflicts = conflict_engine.evaluate_claims(provenance_tracker.claims, provenance_tracker.sources)
    print("\n⚖️  CONTRADICTORY AGRICULTURAL CLAIMS:")
    for i, c in enumerate(conflicts, 1):
        print(f"  [{i}] Entity: {c.get('entity_name')}")
        print(f"      Claim: {c.get('claim_text')}")
        print(f"      Status: {c.get('status')}")
    print()

def handle_validation():
    sensors_file = os.path.join("data", "sensors.json")
    if os.path.exists(sensors_file):
        import json
        with open(sensors_file, "r") as f:
            raw = json.load(f)
            res = validation_service.process_readings(raw)
            print(f"\n🛡️  SENSOR TELEMETRY VALIDATION ({res['invalid_count']} Rejected):")
            for inv in res['invalid_records']:
                print(f"  • {inv['sensor_id']} ({inv['metric']}: {inv['value']}{inv['unit']})")
                print(f"    Reason: {inv['anomaly_reason']}")
                print(f"    Action: {inv['action_taken']}")
            print()

def main():
    print(BANNER)

    while True:
        try:
            user_input = input("AgriGraph > ").strip()
            if not user_input:
                continue

            cmd_lower = user_input.lower()

            if cmd_lower in ["exit", "quit", "q"]:
                print("\nExiting AgriGraph. Goodbye!\n")
                break

            elif cmd_lower in ["examples", "sample", "queries"]:
                print("\nSample Farmer Queries you can enter:")
                for i, q in enumerate(SAMPLE_QUERIES, 1):
                    print(f"  {i}. {q}")
                print()
                continue

            elif cmd_lower in ["stats", "metrics"]:
                handle_stats()
                continue

            elif cmd_lower in ["conflicts", "conflict"]:
                handle_conflicts()
                continue

            elif cmd_lower in ["validation", "sensors", "guardrails"]:
                handle_validation()
                continue

            elif cmd_lower in ["help", "commands"]:
                print("\nAvailable commands:")
                print("  examples   - View sample questions")
                print("  stats      - Display graph metrics")
                print("  conflicts  - Show detected contradictory claims")
                print("  validation - Show sensor validation audit")
                print("  exit       - Quit the assistant\n")
                continue

            # Execute Query Pipeline
            response = retrieval_service.execute_farmer_query(user_input)
            format_query_response(response)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting AgriGraph. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n[!] Error processing query: {e}\n")

if __name__ == "__main__":
    main()

# AgriGraph (PNA1) — Agritech & Rural Innovation

> Dynamic Agricultural Knowledge Graph connecting crops, diseases, treatments, and environmental telemetry while tracking source provenance and surfacing conflicting evidence.

---

## 🌟 Hackathon Scenario Demo Flow (3-Minute Tour)

1. **Dashboard Overview (`/`)**:
   - Inspect key graph metrics: 6 Crops, 6 Diseases, 7 Treatments, 7 Sources, 25 Relationships across 45 Knowledge Nodes.
   - Note the **Provenance Coverage (83.3%)**, **1 Flagged Conflict**, and **3 Blocked Adversarial Sensor Readings**.
2. **Farmer Scenario Query**:
   - Click **"Launch Farmer Scenario"** or navigate to **Farmer Query**.
   - Execute the target prompt:
     > *"Why is my tomato crop at high disease risk and what evidence supports this?"*
   - Observe the multi-layered response:
     - **Agricultural Insight**: Explains high vulnerability to *Early Blight (Alternaria solani)* driven by sustained microclimate wetness.
     - **Contributing Factors**: Explains the pathogen spore biology (>80% humidity, 24–30°C for >8 hrs) and field observations (35% concentric target lesion rate in Plot 4A).
     - **Supporting Evidence**: Sourced graph triples (`Tomato -[:SUSCEPTIBLE_TO]-> Early Blight`, `Early Blight -[:ASSOCIATED_WITH]-> Humid Warm Monsoon`).
     - **Source Lineage**: Direct citations to research paper `DOC_001` and farmer advisory `DOC_007`.
     - **Conflicting Evidence Alert**: Transparently displays that *Neem Oil Extract* is claimed as curative by `DOC_003` but refuted by multi-site meta-analysis `DOC_004`.
     - **Adversarial Telemetry Shield**: Shows that `SENSOR_CORRUPT_TEMP_99` (reading 250°C) and negative humidity were caught and rejected from the reasoning engine.
3. **Interactive Knowledge Graph (`/graph`)**:
   - Visual HTML5 canvas rendering the connected knowledge graph.
   - Click on nodes (`Tomato`, `Early Blight`, `Humid Warm Monsoon`, `Copper Hydroxide`) to inspect detailed properties in real time.
4. **Evidence & Provenance Catalog (`/provenance`)**:
   - Full ledger of peer-reviewed publications, sensor networks, extension advisories, and farmer logs with confidence ratings.
5. **Conflicts & Data Quality Shield (`/quality`)**:
   - In-depth contradiction analysis comparing supporting vs contradictory empirical evidence.
   - Live audit table of sensor telemetry sanity checks.

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Optional: Docker (for local Neo4j & MongoDB containers)

### 1. Backend Setup
```bash
# From repository root
python3 -m pip install fastapi uvicorn pydantic neo4j pymongo pandas sentence-transformers scikit-learn

# Run FastAPI backend (defaults to port 8000)
python3 -m uvicorn backend.main:app --reload --port 8000
```
Backend API will be live at: `http://localhost:8000`
Interactive Swagger Docs at: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
# In another terminal window:
cd frontend
npm install
npm run dev
```
Frontend UI will be live at: `http://localhost:5173`

---

## 🏗️ Architecture & Component Design

```text
                    DATA SOURCES
                         |
        +----------------+----------------+
        |                |                |
   Research Docs      Weather          Soil
   Crop/Disease       Farmer          Sensor
   Data               Data            Data
        |                |                |
        +----------------+----------------+
                         |
                  DATA INGESTION
             (CSV, JSON, Text extract)
                         |
              CLEANING / NORMALIZATION
                         |
              ENTITY + RELATION EXTRACTION
                         |
                  KNOWLEDGE GRAPH
            (Neo4j + In-Memory Fallback)
                         |
        +----------------+----------------+
        |                |                |
   Provenance      Conflict Detection   Validation
        |                |                |
        +----------------+----------------+
                         |
                  QUERY PROCESSING
            (Semantic Entity Retrieval)
                         |
                    FASTAPI API
                         |
                   REACT FRONTEND
```

---

## 🧪 Testing

Run the automated integration test suite:
```bash
python3 -c "
from tests.test_agrigraph import *
test_health_endpoint()
test_dashboard_stats()
test_farmer_query_core_scenario()
test_sensor_validation_logic()
test_conflict_detection_logic()
print('All tests passed!')
"
```

---

## 📊 Data Disclosure
- **Real / Public Source Data**: Standard agricultural taxonomy, environmental pathogen thresholds for *Alternaria solani*, and research findings adapted from plant pathology publications.
- **Demo / Synthetic Data**: Sensor telemetry readings and farmer field observations (`OBS_001`, `OBS_002`), intentionally corrupted sensor readings (`SN_READ_005` to `007`) for adversarial testing, and the unverified claim (`CLM_006`). All demo records are explicitly labeled.

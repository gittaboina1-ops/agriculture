# AgriGraph (PNA1) — Terminal-First Agricultural Knowledge Pipeline

> Dynamic Agricultural Knowledge Graph connecting crops, diseases, treatments, soil conditions, and environmental telemetry while tracking source provenance, surfacing conflicting scientific evidence, and rejecting corrupted sensor data.

---

## 💻 Running the Terminal Interactive Application

To launch the interactive AgriGraph CLI assistant:

```bash
python3 -m backend.cli
```

### CLI Interactive Commands:
- Any natural-language agricultural question (e.g. `What soil conditions are suitable for tomato?`)
- `examples` — List sample queries
- `stats` — Display knowledge graph metrics and Neo4j status
- `conflicts` — View detected conflicting claims (e.g. Neem Oil)
- `validation` — View rejected sensor telemetry audit
- `help` — Show available commands
- `exit` — Quit the application

---

## 🔍 Core Pipeline Architecture

```text
User Query
    ↓
Query Understanding & Intent Detection (backend/retrieval/intent.py)
    ↓
Entity Identification & Semantic Retrieval (backend/retrieval/service.py)
    ↓
Intent-Filtered Knowledge Graph Traversal (backend/graph/service.py)
    ↓
Relevant Subgraph & Relational Triples
    ↓
Source Provenance Retrieval (backend/provenance/tracker.py)
    ↓
Conflict Detection Engine (backend/conflict/engine.py)
    ↓
Sensor Telemetry Validation & Guardrails (backend/validation/validator.py)
    ↓
Evidence Context Construction
    ↓
LLM Grounded Answer Generation (backend/services/llm_service.py)
    ↓
Formatted Terminal Output (backend/cli.py)
```

---

## 🧪 Automated Regression Tests

Run the full automated backend test suite:

```bash
PYTHONPATH=. python3 tests/test_backend_pipeline.py
```

### Test Coverage:
1. **Intent Classification**: Tests all 7 canonical intents (`CROP_DISEASE`, `SOIL_SUITABILITY`, `DISEASE_RISK`, `TREATMENT`, `EVIDENCE_PROVENANCE`, `CONFLICT`, `DATA_QUALITY`).
2. **Soil Query Bug Regression**: Confirms `What soil conditions are suitable for tomato?` strictly traverses `(Crop)-[:SUITABLE_FOR]->(Soil)` and does **not** leak Early Blight or disease risk.
3. **Crop Disease Traversal**: Confirms `(Crop)-[:SUSCEPTIBLE_TO]->(Disease)` paths.
4. **Treatment Retrieval**: Grounded in prophylactic Copper Hydroxide (`DOC_001`) and Bacillus subtilis (`DOC_002`).
5. **Conflict Engine**: Surfaces the Neem Oil debate (`DOC_003` extension advisory vs `DOC_004` meta-analysis).
6. **Data Quality Shield**: Confirms corrupted telemetry (250°C temperature, negative humidity, pH 20) is caught and barred.

---

## 📋 Sample Test Queries

Try entering these directly into the terminal CLI:

1. `What diseases commonly affect tomato?`
   - *Traverses:* `Tomato -[:SUSCEPTIBLE_TO]-> Early Blight, Late Blight, Septoria`
2. `What soil conditions are suitable for tomato?`
   - *Traverses:* `Tomato -[:SUITABLE_FOR]-> Loamy Sand, Alluvial Silt` *(DOC_005)*
3. `Why is my tomato crop at high disease risk?`
   - *Traverses:* `Tomato -> Early Blight -> 88.5% Humidity -> DOC_001, DOC_007`
4. `What treatments are associated with Early Blight?`
   - *Traverses:* `Early Blight -[:TREATED_BY]-> Copper Hydroxide, Chlorothalonil, Bacillus subtilis`
5. `Are there conflicting recommendations for Neem Oil Extract?`
   - *Surfaces:* `DOC_003` (claims effective) vs `DOC_004` (ineffective under >85% humidity)
6. `Are there any invalid sensor readings?`
   - *Rejects:* `SENSOR_CORRUPT_TEMP_99` (250°C), negative humidity, and pH 20

---

## 🚀 Running the Full Web Application (Backend + Frontend)

AgriGraph includes a unified runner that launches both the **FastAPI Backend (port 8000)** and the **React + Vite Frontend (port 5173)** simultaneously:

```bash
python3 run.py
```

Access points:
- **Frontend Web UI**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 🔐 Demo Credentials

The system comes pre-seeded with authenticated accounts:

| Role | Email | Password | Admin Passcode |
|---|---|---|---|
| **Farmer** | `farmer@agrigraph.org` | `farmerpassword123` | *N/A* |
| **Admin** | `admin@agrigraph.org` | `adminpassword123` | `AGRIGRAPH_ADMIN_2026` |

---

## 🌾 Farmer Web Experience
- **Multilingual Support**: Real-time translation into **Telugu**, **Hindi**, and **English** with strict preservation of scientific terms and evidence citations.
- **Voice Input**: Integrated browser Web Speech recognition for voice querying in Telugu, Hindi, or English.
- **Evidence & Provenance**: Every response cites peer-reviewed source IDs (e.g., `DOC_001`, `DOC_002`) and displays verifiable confidence scores.
- **Conflict & Quality Guardrails**: Clear, color-coded alerts when agricultural claims are in scientific dispute or when field sensors transmit anomalous values.

---

## 🔬 Admin Dynamic Knowledge Graph Construction
Admins can upload new agricultural resources (**PDF, CSV, JSON**):
1. **Extraction**: Structured text parsing with page boundary and table preservation.
2. **Chunking & Vector Indexing**: Sentence Transformer vector embeddings with cosine similarity.
3. **Structured Extraction & Normalization**: Entity canonicalization and ontology schema validation.
4. **Provenance & Conflict Auditing**: Checks incoming claims against existing literature.
5. **Graph Insertion**: Dynamic updates to Neo4j / in-memory graph.
6. **Query Readiness**: Ingested knowledge immediately enriches subsequent farmer queries.

---

## 🧪 Comprehensive Automated Verification

AgriGraph includes two end-to-end automated test suites:

```bash
# 1. Test complete query pipeline, intent routing, and regression isolation
PYTHONPATH=. python3 tests/test_backend_pipeline.py

# 2. Test multi-stage dynamic ingestion pipeline (PDF, CSV, JSON, conflicts, graph update)
PYTHONPATH=. python3 -m unittest tests/test_dynamic_ingestion.py
```

---

## ⚙️ Environment Configuration

Configuration variables can be customized in `.env` (refer to `.env.example`):
- `NEO4J_URI` (default: `bolt://localhost:7687`)
- `NEO4J_USER` (default: `neo4j`)
- `NEO4J_PASSWORD` (default: `password`)
- `MONGODB_URI` (default: `mongodb://localhost:27017`)
- `USE_MOCK_FALLBACK` (default: `true` — enables seamless hybrid resilience)


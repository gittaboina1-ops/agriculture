"""
Comprehensive Automated Tests for AgriGraph Dynamic Knowledge Graph Construction Flow:
1. PDF text extraction (valid vs empty/corrupted)
2. Text chunking & metadata preservation
3. Sentence Transformer embedding & local vector indexing
4. Structured LLM / NLP entity & claim extraction
5. Invalid extraction payload / malformed JSON handling
6. Entity normalization (exact, alias, and new entity creation)
7. Relationship validation against ontology schema
8. Provenance tracking & source attachment
9. Duplicate relationship deduplication & multiple evidence retention
10. Conflict detection between opposing claims
11. In-memory / Neo4j graph update
12. End-to-end integration: Ingest PDF -> Query new knowledge -> Verify output
13. Resilient failure handling
"""

import os
import unittest
from backend.ingestion.pdf_extractor import pdf_extractor
from backend.ingestion.chunker import chunker
from backend.ingestion.semantic_index import semantic_index
from backend.ingestion.entity_extractor import entity_extractor
from backend.ingestion.normalizer import entity_normalizer
from backend.ingestion.validator import ingestion_validator
from backend.ingestion.document_service import document_service
from backend.graph.service import graph_service
from backend.provenance.tracker import provenance_tracker
from backend.retrieval.service import retrieval_service

class TestDynamicIngestionPipeline(unittest.TestCase):

    def setUp(self):
        self.test_pdf = "data/test_research_paper.pdf"

    def test_01_pdf_text_extraction(self):
        pages = pdf_extractor.extract_text_from_pdf(self.test_pdf)
        self.assertGreaterEqual(len(pages), 1)
        self.assertIn("Tomato", pages[0]["text"])
        self.assertIn("Early Blight", pages[0]["text"])

    def test_02_pdf_extraction_empty_file_failure(self):
        empty_pdf = "data/empty_test.pdf"
        with open(empty_pdf, "w") as f:
            f.write("")
        with self.assertRaises(ValueError):
            pdf_extractor.extract_text_from_pdf(empty_pdf)
        if os.path.exists(empty_pdf):
            os.remove(empty_pdf)

    def test_03_chunk_generation(self):
        pages = [{"page": 1, "text": "Tomato plants show susceptibility to Early Blight. In humid conditions, leaf wetness accelerates sporulation."}]
        chunks = chunker.chunk_document("DOC_TEST_01", pages)
        self.assertGreaterEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["document_id"], "DOC_TEST_01")
        self.assertEqual(chunks[0]["page"], 1)
        self.assertIn("DOC_TEST_01_CHUNK_", chunks[0]["chunk_id"])

    def test_04_semantic_vector_indexing_and_search(self):
        chunks = [{
            "document_id": "DOC_VEC_01",
            "page": 1,
            "chunk_id": "DOC_VEC_01_CHUNK_001",
            "text": "Bio-fungicides like Bacillus subtilis suppress early blight in open field tomatoes.",
            "section": "Results"
        }]
        semantic_index.index_chunks(chunks, {"title": "Bio-fungicides Trial", "source_type": "Research Paper"})
        results = semantic_index.search_similar("Bacillus subtilis suppression", top_k=2)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["chunk_id"], "DOC_VEC_01_CHUNK_001")

    def test_05_structured_knowledge_extraction(self):
        chunk = {
            "chunk_id": "CHK_01",
            "text": "Tomato plants are susceptible to Early Blight caused by Alternaria solani. High humidity increases the disease risk."
        }
        res = entity_extractor.extract_from_chunk(chunk)
        self.assertIn("entities", res)
        self.assertIn("relationships", res)
        self.assertIn("claims", res)
        
        ent_names = [e["name"] for e in res["entities"]]
        self.assertIn("Tomato", ent_names)
        self.assertIn("Early Blight", ent_names)

        rels = [(r["subject"], r["relation"], r["object"]) for r in res["relationships"]]
        self.assertIn(("Tomato", "SUSCEPTIBLE_TO", "Early Blight"), rels)

    def test_06_invalid_extraction_payload_handling(self):
        invalid_payload = "Not a json"
        valid, msg, cleaned = ingestion_validator.validate_extraction_payload(invalid_payload)
        self.assertFalse(valid)

        malformed_dict = {"entities": "not a list"}
        valid, msg, cleaned = ingestion_validator.validate_extraction_payload(malformed_dict)
        self.assertFalse(valid)

    def test_07_entity_normalization(self):
        # Exact match
        norm1 = entity_normalizer.normalize_entity({"name": "Tomato", "type": "Crop"})
        self.assertEqual(norm1["name"], "Tomato")
        self.assertFalse(norm1["is_new"])

        # Alias match
        norm2 = entity_normalizer.normalize_entity({"name": "Solanum lycopersicum", "type": "Crop"})
        self.assertEqual(norm2["name"], "Tomato")
        self.assertFalse(norm2["is_new"])

        # Novel entity
        norm3 = entity_normalizer.normalize_entity({"name": "Anthracnose Rot", "type": "Disease"})
        self.assertEqual(norm3["name"], "Anthracnose Rot")
        self.assertTrue(norm3["is_new"])

    def test_08_ontology_relationship_validation(self):
        sub_crop = {"label": "Crop", "name": "Tomato"}
        obj_dis = {"label": "Disease", "name": "Early Blight"}
        obj_soil = {"label": "Soil", "name": "Loamy Sand"}

        # Valid triple: Crop -> SUSCEPTIBLE_TO -> Disease
        is_val, _ = ingestion_validator.validate_relationship(sub_crop, "SUSCEPTIBLE_TO", obj_dis)
        self.assertTrue(is_val)

        # Invalid triple: Crop -> SUSCEPTIBLE_TO -> Soil
        is_val, reason = ingestion_validator.validate_relationship(sub_crop, "SUSCEPTIBLE_TO", obj_soil)
        self.assertFalse(is_val)

        # Malformed relation: Crop -> RANDOM_RELATION -> Soil
        is_val, reason = ingestion_validator.validate_relationship(sub_crop, "RANDOM_RELATION", obj_soil)
        self.assertFalse(is_val)

    def test_09_duplicate_relationship_handling(self):
        # When same relation is ingested from another doc, duplicate edge count is skipped and provenance is appended
        doc_entry = document_service.register_document(
            file_path="data/test_research_paper.pdf",
            filename="duplicate_test.pdf",
            title="Duplicate Test Paper"
        )
        res = document_service.process_document(doc_entry["document_id"])
        self.assertGreaterEqual(res["stats"]["duplicates_skipped"], 1)

    def test_10_conflict_detection_on_ingestion(self):
        # Ingestion of test_research_paper.pdf asserts that Neem Oil Extract was ineffective under high humidity
        # This opposes DOC_003's claim of curative efficacy
        conflicts = [c for c in provenance_tracker.claims if c.get("status") == "CONFLICTING"]
        self.assertGreaterEqual(len(conflicts), 1)

    def test_11_end_to_end_ingestion_and_farmer_query(self):
        # Step 1: Ingest research paper with novel disease
        doc_entry = document_service.register_document(
            file_path="data/new_disease_paper.pdf",
            filename="new_disease_paper.pdf",
            title="Anthracnose Rot Susceptibility in Tomato"
        )
        res = document_service.process_document(doc_entry["document_id"])
        self.assertEqual(res["status"], "COMPLETED")
        self.assertGreaterEqual(res["stats"]["new_relationships"], 1)

        # Step 2: Query knowledge base
        query = "What diseases affect tomato?"
        ans = retrieval_service.execute_farmer_query(query)

        # Step 3: Verify novel disease appears with provenance
        insight = ans["agricultural_insight"]
        self.assertIn("Anthracnose Rot", insight)
        
        evidence_objects = [ev["object"] for ev in ans["evidence"]]
        self.assertIn("Anthracnose Rot", evidence_objects)

        prov_sources = [s["source_id"] for s in ans["sources"]]
        self.assertIn(doc_entry["document_id"], prov_sources)

    def test_12_csv_and_json_ingestion(self):
        # Create small test CSV file
        csv_path = "data/test_agri_data.csv"
        with open(csv_path, "w") as f:
            f.write("crop,disease,treatment,notes\nTomato,Bacterial Spot,Copper Fungicide,Protective spray against spot\n")

        doc_csv = document_service.register_document(
            file_path=csv_path,
            filename="test_agri_data.csv",
            title="Bacterial Spot Management Guidelines",
            source_type="Agronomic Guide"
        )
        res_csv = document_service.process_document(doc_csv["document_id"])
        self.assertEqual(res_csv["status"], "COMPLETED")
        self.assertGreaterEqual(res_csv["stats"]["pages_processed"], 1)

        # Create small test JSON file
        json_path = "data/test_agri_data.json"
        with open(json_path, "w") as f:
            f.write('[{"subject": "Tomato", "relation": "SUSCEPTIBLE_TO", "object": "Early Blight", "notes": "Fungal pathogen"}]')

        doc_json = document_service.register_document(
            file_path=json_path,
            filename="test_agri_data.json",
            title="JSON Diagnostic Feed",
            source_type="Sensor / Data Feed"
        )
        res_json = document_service.process_document(doc_json["document_id"])
        self.assertEqual(res_json["status"], "COMPLETED")
        self.assertGreaterEqual(res_json["stats"]["pages_processed"], 1)

        # Cleanup
        if os.path.exists(csv_path):
            os.remove(csv_path)
        if os.path.exists(json_path):
            os.remove(json_path)

if __name__ == "__main__":
    unittest.main()


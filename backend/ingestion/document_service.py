"""
Admin Document Ingestion Service & Knowledge Graph Construction Orchestrator.
Coordinates the complete pipeline:
PDF Upload -> Text Extraction -> Chunking -> Embeddings & Vector Index ->
LLM/NLP Extraction -> Entity Normalization -> Schema Validation ->
Provenance Attachment -> Conflict Detection -> Knowledge Graph Update ->
Query Readiness.
"""

import os
import time
import json
import logging
import uuid
from typing import Dict, Any, List, Optional

from backend.ingestion.pdf_extractor import pdf_extractor
from backend.ingestion.chunker import chunker
from backend.ingestion.semantic_index import semantic_index
from backend.ingestion.entity_extractor import entity_extractor
from backend.ingestion.normalizer import entity_normalizer
from backend.ingestion.validator import ingestion_validator
from backend.graph.service import graph_service
from backend.provenance.tracker import provenance_tracker
from backend.conflict.engine import conflict_engine

logger = logging.getLogger("document_service")

class DocumentIngestionService:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
        # Store in-memory document state tracking
        self.documents: Dict[str, Dict[str, Any]] = {}
        self._seed_existing_sources()

    def _seed_existing_sources(self):
        """Registers existing DOC_001..DOC_007 sources in the document tracker."""
        for s in provenance_tracker.get_all_sources():
            sid = s.get("source_id")
            if sid and sid not in self.documents:
                self.documents[sid] = {
                    "document_id": sid,
                    "title": s.get("title", ""),
                    "source_type": s.get("source_type", "Research Paper"),
                    "status": "COMPLETED",
                    "uploaded_at": "2026-09-30T00:00:00Z",
                    "confidence_score": s.get("confidence_score", 0.95),
                    "file_path": None,
                    "stats": {
                        "pages": 1,
                        "chunks": 1,
                        "entities_extracted": 0,
                        "relationships_extracted": 0,
                        "claims_extracted": 0,
                        "new_nodes": 0,
                        "new_relationships": 0,
                        "duplicates_skipped": 0,
                        "conflicts_detected": 0,
                        "rejected": 0
                    }
                }

    def generate_next_document_id(self) -> str:
        existing_ids = list(self.documents.keys()) + list(provenance_tracker.sources.keys())
        doc_nums = []
        for sid in existing_ids:
            if sid.startswith("DOC_"):
                try:
                    num = int(sid.split("_")[1])
                    doc_nums.append(num)
                except Exception:
                    pass
        next_num = max(doc_nums, default=7) + 1
        return f"DOC_{next_num:03d}"

    def register_document(
        self,
        file_path: str,
        filename: str,
        title: Optional[str] = None,
        source_type: str = "Research Paper",
        authors: str = "Unknown Author",
        publication_year: int = 2026,
        confidence_score: float = 0.92
    ) -> Dict[str, Any]:
        """
        Registers an uploaded document and prepares it for processing.
        """
        doc_id = self.generate_next_document_id()
        doc_title = title or filename.replace("_", " ").replace(".pdf", "").title()
        
        doc_entry = {
            "document_id": doc_id,
            "filename": filename,
            "title": doc_title,
            "source_type": source_type,
            "authors": authors,
            "publication_year": publication_year,
            "confidence_score": confidence_score,
            "file_path": file_path,
            "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "UPLOADED",
            "error": None,
            "stats": {}
        }
        self.documents[doc_id] = doc_entry
        return doc_entry

    def _extract_pages_from_file(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """
        Extracts textual content page-by-page or record-by-record supporting:
        - PDF documents via robust pdf_extractor
        - CSV spreadsheets (parsed into human-readable, schema-grounded records)
        - JSON structured datasets
        - Plain text / Markdown
        """
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            return pdf_extractor.extract_text_from_pdf(file_path)
        
        elif ext == ".csv":
            import pandas as pd
            df = pd.read_csv(file_path)
            pages = []
            chunk_rows = 15
            for page_idx, start_row in enumerate(range(0, len(df), chunk_rows), 1):
                subset = df.iloc[start_row:start_row + chunk_rows]
                text_lines = []
                for _, row in subset.iterrows():
                    row_parts = [f"{col}: {val}" for col, val in row.items() if pd.notna(val)]
                    text_lines.append("; ".join(row_parts))
                page_text = f"Agricultural Dataset Record (Sheet {page_idx}):\n" + "\n".join(text_lines)
                pages.append({"page": page_idx, "text": page_text})
            return pages if pages else [{"page": 1, "text": "Empty CSV file."}]

        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            pages = []
            if isinstance(data, list):
                chunk_items = 10
                for page_idx, i in enumerate(range(0, len(data), chunk_items), 1):
                    batch = data[i:i + chunk_items]
                    page_text = f"Agricultural JSON Records (Batch {page_idx}):\n" + json.dumps(batch, indent=2)
                    pages.append({"page": page_idx, "text": page_text})
            else:
                pages.append({"page": 1, "text": json.dumps(data, indent=2)})
            return pages

        else:
            # Fallback for plain text, txt, md
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return [{"page": 1, "text": content}]

    def process_document(self, document_id: str) -> Dict[str, Any]:
        """
        Executes the complete multi-stage knowledge extraction and graph construction pipeline.
        """
        doc = self.documents.get(document_id)
        if not doc:
            raise ValueError(f"Document ID {document_id} not registered.")

        start_time = time.time()
        file_path = doc["file_path"]

        stats = {
            "pages_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "entities_extracted": 0,
            "relationships_extracted": 0,
            "claims_extracted": 0,
            "new_nodes": 0,
            "new_relationships": 0,
            "duplicates_skipped": 0,
            "conflicts_detected": 0,
            "rejected_relationships": 0,
            "processing_time_sec": 0.0
        }

        try:
            # 1. EXTRACTING
            doc["status"] = "EXTRACTING"
            pages = self._extract_pages_from_file(file_path, doc.get("filename", "document.pdf"))
            stats["pages_processed"] = len(pages)

            # 2. CHUNKING
            doc["status"] = "CHUNKING"
            chunks = chunker.chunk_document(document_id, pages)
            stats["chunks_created"] = len(chunks)

            # 3. EMBEDDING & SEMANTIC INDEXING
            doc["status"] = "EMBEDDING"
            source_meta = {
                "title": doc["title"],
                "source_type": doc["source_type"]
            }
            semantic_index.index_chunks(chunks, source_meta)
            stats["embeddings_generated"] = len(chunks)

            # 4. LLM / NLP STRUCTURED KNOWLEDGE EXTRACTION
            doc["status"] = "EXTRACTING_KNOWLEDGE"
            raw_extractions = []
            for c in chunks:
                ext = entity_extractor.extract_from_chunk(c)
                valid, msg, cleaned = ingestion_validator.validate_extraction_payload(ext)
                if valid:
                    raw_extractions.append({
                        "chunk": c,
                        "payload": cleaned
                    })

            # 5. NORMALIZING & VALIDATING
            doc["status"] = "NORMALIZING"
            normalized_entities = {} # raw_name -> normalized entity dict
            validated_relationships = []
            extracted_claims = []

            for item in raw_extractions:
                c = item["chunk"]
                payload = item["payload"]

                # Normalize entities
                for raw_ent in payload.get("entities", []):
                    r_name = raw_ent["name"]
                    if r_name not in normalized_entities:
                        norm = entity_normalizer.normalize_entity(raw_ent)
                        normalized_entities[r_name] = norm
                        stats["entities_extracted"] += 1

                # Normalize and validate relationships
                for raw_rel in payload.get("relationships", []):
                    stats["relationships_extracted"] += 1
                    s_name = raw_rel["subject"]
                    o_name = raw_rel["object"]
                    r_type = raw_rel["relation"]

                    sub_norm = normalized_entities.get(s_name) or entity_normalizer.normalize_entity({"name": s_name, "type": "General"})
                    obj_norm = normalized_entities.get(o_name) or entity_normalizer.normalize_entity({"name": o_name, "type": "General"})

                    # Validate relationship with ontology
                    is_valid, reason = ingestion_validator.validate_relationship(sub_norm, r_type, obj_norm)
                    if is_valid:
                        validated_relationships.append({
                            "source_id": sub_norm["id"],
                            "source_name": sub_norm["name"],
                            "target_id": obj_norm["id"],
                            "target_name": obj_norm["name"],
                            "relationship": r_type,
                            "chunk_id": c["chunk_id"],
                            "page": c["page"],
                            "evidence": c["text"][:200]
                        })
                    else:
                        stats["rejected_relationships"] += 1

                # Collect claims
                for raw_claim in payload.get("claims", []):
                    stats["claims_extracted"] += 1
                    claim_id = f"CLM_{document_id}_{len(extracted_claims)+1:03d}"
                    extracted_claims.append({
                        "claim_id": claim_id,
                        "subject": raw_claim["subject"],
                        "predicate": raw_claim["predicate"],
                        "object": raw_claim["object"],
                        "claim_text": raw_claim["statement"],
                        "polarity": raw_claim.get("polarity", "SUPPORTS"),
                        "primary_source_id": document_id,
                        "supporting_source_ids": document_id if raw_claim.get("polarity") == "SUPPORTS" else "",
                        "contradicting_source_ids": document_id if raw_claim.get("polarity") == "CONTRADICTS" else "",
                        "chunk_id": c["chunk_id"],
                        "page": c["page"],
                        "evidence_text": raw_claim.get("evidence_text", c["text"][:200]),
                        "status": "VERIFIED" if raw_claim.get("polarity") == "SUPPORTS" else "CONFLICTING",
                        "confidence": doc["confidence_score"]
                    })

            # 6. ATTACH PROVENANCE SOURCE
            provenance_tracker.sources[document_id] = {
                "source_id": document_id,
                "title": doc["title"],
                "source_type": doc["source_type"],
                "authors_or_publisher": doc["authors"],
                "publication_year": doc["publication_year"],
                "confidence_score": doc["confidence_score"],
                "summary": f"Uploaded document: {doc['filename']}",
                "is_synthetic": False
            }

            # 7. CONFLICT DETECTION
            doc["status"] = "CHECKING_CONFLICTS"
            detected_conflicts = []
            for claim in extracted_claims:
                # Compare against existing claims in provenance_tracker
                for ex_claim in provenance_tracker.claims:
                    # Check matching subject and predicate/relationship
                    subj_match = claim["subject"].lower() in ex_claim.get("claim_text", "").lower() or ex_claim.get("entity_name", "").lower() in claim["subject"].lower()
                    if subj_match:
                        # Opposing polarities
                        if claim["polarity"] == "CONTRADICTS" and ex_claim.get("status") == "VERIFIED":
                            stats["conflicts_detected"] += 1
                            claim["status"] = "CONFLICTING"
                            claim["conflicting_source_id"] = ex_claim.get("primary_source_id")
                            ex_claim["status"] = "CONFLICTING"
                            ex_claim["contradicting_source_ids"] = f"{ex_claim.get('contradicting_source_ids', '')};{document_id}".strip(";")
                            detected_conflicts.append({
                                "claim_id": claim["claim_id"],
                                "entity_name": claim["subject"],
                                "claim_text": claim["claim_text"],
                                "supporting_sources": [provenance_tracker.get_source(ex_claim.get("primary_source_id"))],
                                "contradicting_sources": [provenance_tracker.get_source(document_id)],
                                "status": "CONFLICTING EVIDENCE DETECTED"
                            })

                provenance_tracker.claims.append(claim)

            # 8. KNOWLEDGE GRAPH UPDATE (NEO4J + IN-MEMORY)
            doc["status"] = "UPDATING_GRAPH"

            # Insert / Merge Nodes
            for norm in normalized_entities.values():
                nid = norm["id"]
                if nid not in graph_service.nodes:
                    graph_service._add_node(
                        node_id=nid,
                        label=norm["label"],
                        name=norm["name"],
                        properties={
                            "provenance": document_id,
                            "original_name": norm.get("original_name", norm["name"]),
                            "description": f"Extracted from {doc['title']}"
                        }
                    )
                    stats["new_nodes"] += 1
                    # Also write to live Neo4j if connected
                    if graph_service.connected_to_neo4j and graph_service.driver:
                        try:
                            with graph_service.driver.session() as session:
                                session.run(f"""
                                    MERGE (n:{norm['label']} {{id: $id}})
                                    SET n.name = $name, n.provenance = $prov
                                """, id=nid, name=norm["name"], prov=document_id)
                        except Exception as ne:
                            logger.warning(f"Neo4j node insert failed: {ne}")

            # Insert Relationships (Deduplicating)
            for v_rel in validated_relationships:
                s_id = v_rel["source_id"]
                t_id = v_rel["target_id"]
                rel_type = v_rel["relationship"]

                # Check if relationship already exists
                existing_edge = next((
                    e for e in graph_service.edges 
                    if e["source"] == s_id and e["target"] == t_id and e["relationship"] == rel_type
                ), None)

                if existing_edge:
                    stats["duplicates_skipped"] += 1
                    # Append provenance to existing edge metadata
                    curr_prov = existing_edge.get("properties", {}).get("provenance", "")
                    if document_id not in curr_prov:
                        existing_edge["properties"]["provenance"] = f"{curr_prov}, {document_id}".strip(", ")
                else:
                    graph_service._add_edge(
                        source_id=s_id,
                        target_id=t_id,
                        relationship=rel_type,
                        properties={
                            "provenance": document_id,
                            "page": v_rel["page"],
                            "chunk_id": v_rel["chunk_id"],
                            "evidence": v_rel["evidence"]
                        }
                    )
                    stats["new_relationships"] += 1
                    # Also write to live Neo4j if connected
                    if graph_service.connected_to_neo4j and graph_service.driver:
                        try:
                            with graph_service.driver.session() as session:
                                session.run(f"""
                                    MATCH (s {{id: $s_id}}), (t {{id: $t_id}})
                                    MERGE (s)-[r:{rel_type}]->(t)
                                    SET r.provenance = $prov, r.chunk_id = $cid
                                """, s_id=s_id, t_id=t_id, prov=document_id, cid=v_rel["chunk_id"])
                        except Exception as ne:
                            logger.warning(f"Neo4j relationship insert failed: {ne}")

            stats["processing_time_sec"] = round(time.time() - start_time, 2)
            doc["status"] = "COMPLETED"
            doc["stats"] = stats
            doc["conflicts"] = detected_conflicts

            return {
                "document_id": document_id,
                "status": "COMPLETED",
                "stats": stats,
                "conflicts": detected_conflicts
            }

        except Exception as e:
            logger.error(f"Document processing failed for {document_id}: {e}", exc_info=True)
            doc["status"] = "FAILED"
            doc["error"] = str(e)
            doc["stats"] = stats
            raise e

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        return self.documents.get(document_id)

    def list_documents(self) -> List[Dict[str, Any]]:
        return list(self.documents.values())

document_service = DocumentIngestionService()

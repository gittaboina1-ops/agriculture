"""
Dedicated local semantic vector index for document chunks.
Uses SQLite for persistent metadata and numpy for cosine similarity vector operations.
Integrates with SentenceTransformer (sentence-transformers/all-MiniLM-L6-v2) or fallback.
"""

import os
import json
import sqlite3
import numpy as np
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("semantic_index")

class SemanticChunkIndex:
    def __init__(self, db_path: str = "data/semantic_index/chunks.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.encoder = None
        self._init_db()

    def attach_encoder(self, encoder):
        self.encoder = encoder

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT,
                    page INTEGER,
                    section TEXT,
                    text TEXT,
                    source_title TEXT,
                    source_type TEXT,
                    embedding_json TEXT
                )
            """)
            conn.commit()

    def index_chunks(self, chunks: List[Dict[str, Any]], source_metadata: Optional[Dict[str, Any]] = None):
        """
        Embeds chunks and writes them to the SQLite vector store.
        """
        if not chunks:
            return

        source_meta = source_metadata or {}
        doc_id = chunks[0].get("document_id", "DOC_UNKNOWN")
        source_title = source_meta.get("title", f"Document {doc_id}")
        source_type = source_meta.get("source_type", "Research Paper")

        texts = [c["text"] for c in chunks]
        embeddings = []

        if self.encoder:
            try:
                raw_embs = self.encoder.encode(texts, normalize_embeddings=True)
                embeddings = [e.tolist() for e in raw_embs]
            except Exception as e:
                logger.warning(f"Embedding failed: {e}. Storing empty embeddings.")
                embeddings = [[] for _ in texts]
        else:
            embeddings = [[] for _ in texts]

        with self._get_connection() as conn:
            for c, emb in zip(chunks, embeddings):
                conn.execute("""
                    INSERT OR REPLACE INTO document_chunks 
                    (chunk_id, document_id, page, section, text, source_title, source_type, embedding_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    c["chunk_id"],
                    c["document_id"],
                    c["page"],
                    c.get("section", "Body"),
                    c["text"],
                    source_title,
                    source_type,
                    json.dumps(emb)
                ))
            conn.commit()

    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search against indexed chunks using cosine similarity.
        Falls back to keyword matching if embeddings are absent.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chunk_id, document_id, page, section, text, source_title, source_type, embedding_json FROM document_chunks")
            rows = cursor.fetchall()

        if not rows:
            return []

        results = []

        # Try vector search if encoder available
        if self.encoder:
            try:
                q_emb = self.encoder.encode([query], normalize_embeddings=True)[0]
                scored = []
                for row in rows:
                    cid, did, page, section, text, stitle, stype, emb_str = row
                    emb = json.loads(emb_str)
                    if emb:
                        emb_arr = np.array(emb, dtype=np.float32)
                        score = float(np.dot(q_emb, emb_arr))
                    else:
                        score = 0.0
                    scored.append((score, {
                        "chunk_id": cid,
                        "document_id": did,
                        "page": page,
                        "section": section,
                        "text": text,
                        "source_title": stitle,
                        "source_type": stype,
                        "similarity_score": round(score, 4)
                    }))
                scored.sort(key=lambda x: x[0], reverse=True)
                return [item[1] for item in scored[:top_k] if item[0] > 0.25]
            except Exception as e:
                logger.warning(f"Vector search calculation error: {e}. Falling back to lexical scan.")

        # Fallback lexical keyword match
        q_words = set(query.lower().split())
        lex_scored = []
        for row in rows:
            cid, did, page, section, text, stitle, stype, _ = row
            text_lower = text.lower()
            overlap = sum(1 for w in q_words if w in text_lower)
            score = round(overlap / max(len(q_words), 1), 3)
            if score > 0.1:
                lex_scored.append((score, {
                    "chunk_id": cid,
                    "document_id": did,
                    "page": page,
                    "section": section,
                    "text": text,
                    "source_title": stitle,
                    "source_type": stype,
                    "similarity_score": score
                }))
        lex_scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in lex_scored[:top_k]]

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chunk_id, document_id, page, section, text, source_title, source_type FROM document_chunks WHERE chunk_id = ?", (chunk_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "chunk_id": row[0],
                    "document_id": row[1],
                    "page": row[2],
                    "section": row[3],
                    "text": row[4],
                    "source_title": row[5],
                    "source_type": row[6]
                }
        return None

    def get_total_chunks(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM document_chunks")
            return cursor.fetchone()[0]

semantic_index = SemanticChunkIndex()

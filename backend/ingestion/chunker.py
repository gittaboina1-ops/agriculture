"""
Text chunking module with metadata & page boundary preservation.
"""

import re
from typing import List, Dict, Any

class DocumentChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 80):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, document_id: str, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Splits page text into manageable chunks while preserving page provenance.
        Returns:
            List of dicts: [
                {
                    "document_id": str,
                    "page": int,
                    "chunk_id": str,
                    "chunk_index": int,
                    "text": str,
                    "section": str
                }
            ]
        """
        chunks = []
        global_chunk_idx = 1

        for p in pages:
            page_num = p.get("page", 1)
            raw_text = p.get("text", "").strip()
            if not raw_text:
                continue

            # Split into sentences or paragraphs first
            paragraphs = [para.strip() for para in raw_text.split("\n\n") if para.strip()]
            if not paragraphs:
                paragraphs = [raw_text]

            current_chunk = ""
            current_section = "General / Body"

            for para in paragraphs:
                # Detect possible section header (e.g., Abstract, Introduction, Results, Discussion)
                if len(para) < 60 and any(h in para.lower() for h in ["abstract", "introduction", "method", "result", "discussion", "conclusion", "efficacy"]):
                    current_section = para

                words = para.split()
                for word in words:
                    if len(current_chunk) + len(word) + 1 <= self.chunk_size:
                        current_chunk = f"{current_chunk} {word}".strip()
                    else:
                        if current_chunk:
                            cid = f"{document_id}_CHUNK_{global_chunk_idx:03d}"
                            chunks.append({
                                "document_id": document_id,
                                "page": page_num,
                                "chunk_id": cid,
                                "chunk_index": global_chunk_idx,
                                "text": current_chunk,
                                "section": current_section
                            })
                            global_chunk_idx += 1
                            # Maintain overlap from tail of current_chunk
                            overlap_words = current_chunk.split()[-15:]
                            current_chunk = " ".join(overlap_words) + f" {word}"
                        else:
                            current_chunk = word

            if current_chunk.strip():
                cid = f"{document_id}_CHUNK_{global_chunk_idx:03d}"
                chunks.append({
                    "document_id": document_id,
                    "page": page_num,
                    "chunk_id": cid,
                    "chunk_index": global_chunk_idx,
                    "text": current_chunk.strip(),
                    "section": current_section
                })
                global_chunk_idx += 1

        return chunks

chunker = DocumentChunker()

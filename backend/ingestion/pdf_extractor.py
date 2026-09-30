"""
Robust PDF text extractor module.
Supports:
1. pdfplumber (primary if installed)
2. pypdf / PyPDF2 (secondary if installed)
3. Built-in resilient PDF text stream decompressor & parser (zero external dependency fallback)
"""

import os
import re
import zlib
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("pdf_extractor")

class PDFExtractor:
    def __init__(self):
        self.preferred_engine = "auto"

    def extract_text_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text page-by-page from a PDF file.
        Returns:
            List of dicts: [{"document_id": ..., "page": int, "text": str}]
        Raises:
            ValueError: If file is missing, invalid, or has no extractable text.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("TEXT_EXTRACTION_FAILED: Empty file provided.")

        pages_extracted = []

        # 1. Try pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for idx, p in enumerate(pdf.pages, 1):
                    txt = p.extract_text() or ""
                    if txt.strip():
                        pages_extracted.append({"page": idx, "text": txt.strip()})
            if pages_extracted:
                return pages_extracted
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}. Trying fallback.")

        # 2. Try pypdf / PyPDF2
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            for idx, p in enumerate(reader.pages, 1):
                txt = p.extract_text() or ""
                if txt.strip():
                    pages_extracted.append({"page": idx, "text": txt.strip()})
            if pages_extracted:
                return pages_extracted
        except ImportError:
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                for idx, p in enumerate(reader.pages, 1):
                    txt = p.extract_text() or ""
                    if txt.strip():
                        pages_extracted.append({"page": idx, "text": txt.strip()})
                if pages_extracted:
                    return pages_extracted
            except ImportError:
                pass
        except Exception as e:
            logger.warning(f"PyPDF2/pypdf extraction failed: {e}. Trying built-in fallback.")

        # 3. Built-in resilient PDF text stream parser
        pages_extracted = self._extract_raw_pdf_streams(file_path)
        if not pages_extracted:
            raise ValueError("TEXT_EXTRACTION_FAILED: No extractable text found in PDF document.")

        return pages_extracted

    def _extract_raw_pdf_streams(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Decompresses and extracts string literals from FlateDecode and raw stream blocks.
        """
        with open(file_path, "rb") as f:
            content = f.read()

        # Check PDF signature
        if not content.startswith(b"%PDF"):
            # If plain text file provided with .pdf extension or plain text format
            try:
                plain_txt = content.decode("utf-8", errors="ignore").strip()
                if plain_txt and len(plain_txt) > 20:
                    return [{"page": 1, "text": plain_txt}]
            except Exception:
                pass
            raise ValueError("TEXT_EXTRACTION_FAILED: Not a valid PDF document header.")

        # Find stream ... endstream blocks
        stream_matches = list(re.finditer(b"stream[\r\n]+(.*?)[\r\n]+endstream", content, re.DOTALL))
        extracted_texts = []
        page_num = 1

        for match in stream_matches:
            raw_stream = match.group(1)
            decompressed = None
            try:
                decompressed = zlib.decompress(raw_stream)
            except Exception:
                try:
                    decompressed = zlib.decompress(raw_stream, -15)
                except Exception:
                    decompressed = raw_stream

            if decompressed:
                try:
                    stream_str = decompressed.decode("latin1", errors="ignore")
                    # Extract text inside parentheses in TJ or Tj operators: (text) Tj or [(t1) 20 (t2)] TJ
                    tj_matches = re.findall(r"\(([^)]+)\)\s*(?:Tj|')", stream_str)
                    array_matches = re.findall(r"\[([^\]]+)\]\s*TJ", stream_str)
                    for arr in array_matches:
                        inner_texts = re.findall(r"\(([^)]+)\)", arr)
                        if inner_texts:
                            tj_matches.extend(inner_texts)

                    if tj_matches:
                        page_text = " ".join(tj_matches)
                        # Clean up escaped chars
                        page_text = page_text.replace("\\(", "(").replace("\\)", ")").replace("\\n", "\n")
                        # Normalize whitespaces
                        page_text = re.sub(r"\s+", " ", page_text).strip()
                        if len(page_text) > 20:
                            extracted_texts.append(page_text)
                except Exception:
                    continue

        if not extracted_texts:
            # Fallback: scan for any readable text inside the PDF body
            text_blocks = re.findall(rb"\(([^)]{10,})\)", content)
            for b in text_blocks:
                t = b.decode("latin1", errors="ignore").strip()
                if len(t) > 20 and not t.startswith("/"):
                    extracted_texts.append(t)

        pages = []
        for idx, txt in enumerate(extracted_texts, 1):
            pages.append({"page": idx, "text": txt})

        return pages

pdf_extractor = PDFExtractor()

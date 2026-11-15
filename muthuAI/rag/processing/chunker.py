"""
MuthuAI Phase 4 — rag/processing/chunker.py

Smart Chunking Strategy:
Splits document text into semantic chunks while preserving paragraph boundaries,
section headings, lists, and metadata.
"""

from __future__ import annotations
import re
from utils.logger import get_logger

log = get_logger("muthuai.rag.chunker")


class TextChunker:
    """
    Splits document sections into chunks with configurable size and overlap.
    """

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text_or_page: str | dict) -> list:
        """Convenience chunk method accepting raw string or page dict."""
        if isinstance(text_or_page, str):
            page_data = {"text": text_or_page, "file_name": "document", "page_number": 1}
            return [c["text"] for c in self.chunk_document_page(page_data)]
        elif isinstance(text_or_page, dict):
            return self.chunk_document_page(text_or_page)
        return []

    def chunk_document_page(self, page_data: dict) -> list[dict]:
        """
        Split a page/section block into semantic chunks.
        Returns list of chunks containing text and enriched metadata.
        """
        text = page_data.get("text", "").strip()
        if not text:
            return []

        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para_clean = para.strip()
            if not para_clean:
                continue

            para_len = len(para_clean)
            if current_length + para_len > self.chunk_size and current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(self._create_chunk(chunk_text, page_data, len(chunks)))

                # Keep last paragraph for overlap
                overlap_text = current_chunk[-1] if current_chunk else ""
                current_chunk = [overlap_text, para_clean] if len(overlap_text) < self.chunk_overlap else [para_clean]
                current_length = sum(len(p) for p in current_chunk)
            else:
                current_chunk.append(para_clean)
                current_length += para_len

        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(self._create_chunk(chunk_text, page_data, len(chunks)))

        log.debug("Chunked %s (Page %s) into %d chunks.",
                  page_data.get("file_name"), page_data.get("page_number"), len(chunks))
        return chunks

    def _create_chunk(self, text: str, page_data: dict, index: int) -> dict:
        meta = page_data.get("metadata", {})
        fname = page_data.get("file_name") or meta.get("file_name", "")
        fpath = page_data.get("file_path") or meta.get("file_path", "")
        ftype = page_data.get("file_type") or meta.get("file_type", "")
        pnum = page_data.get("page_number") or meta.get("page_number", 1)
        sect = page_data.get("section") or meta.get("section", "")
        return {
            "text": text,
            "metadata": {
                "file_name": fname,
                "file_path": fpath,
                "file_type": ftype,
                "page_number": pnum,
                "section": sect,
                "chunk_index": index,
                "source": f"{fname} (Page {pnum})",
            }
        }


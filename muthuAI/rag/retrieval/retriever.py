"""
MuthuAI Phase 4 — rag/retrieval/retriever.py

Semantic RAG Retriever.
Embeds user question, queries VectorStore, ranks chunks, and formats source metadata context.
"""

from __future__ import annotations
from rag.embeddings.embedder import LocalEmbedder
from rag.storage.vector_store import VectorStore
from utils.logger import get_logger

log = get_logger("muthuai.rag.retriever")


class RAGRetriever:
    """
    Retrieves and ranks relevant document chunks for Gemini context.
    """

    def __init__(
        self,
        embedder: LocalEmbedder | None = None,
        vector_store: VectorStore | None = None
    ) -> None:
        self._embedder = embedder or LocalEmbedder()
        self._store = vector_store or VectorStore()

    def retrieve(self, question: str, top_k: int = 4, min_similarity: float = 0.3) -> list[dict]:
        """
        Embed question, retrieve top_k chunks, and return results with cosine similarity filtering.
        """
        if self._store.count() == 0:
            log.info("RAG vector store is empty. No document chunks retrieved.")
            return []

        log.info("Retrieving RAG chunks for question: %r", question)
        query_vec = self._embedder.embed_query(question)
        raw_chunks = self._store.query(query_vec, top_k=top_k)
        chunks = [c for c in raw_chunks if c.get("score", 0.0) >= min_similarity]
        log.info("Retrieved %d relevant RAG chunks (out of %d raw, threshold=%.2f).", len(chunks), len(raw_chunks), min_similarity)
        return chunks

    def format_context(self, chunks: list[dict]) -> str:
        """
        Format retrieved chunks into structured context block with clear source metadata.
        """
        if not chunks:
            return ""

        blocks = ["### RETRIEVED PERSONAL DOCUMENT CONTEXT:\n"]
        for idx, item in enumerate(chunks, 1):
            text = item.get("text", "")
            meta = item.get("metadata", {})
            file_name = meta.get("file_name", "Unknown File")
            page_num = meta.get("page_number", 1)
            section = meta.get("section", f"Page {page_num}")
            score = item.get("score", 0.0)

            blocks.append(
                f"SOURCE {idx}:\n"
                f"Document: {file_name}\n"
                f"Page: {page_num}\n"
                f"Section: {section}\n"
                f"Relevance Score: {score}\n"
                f"Content:\n{text}\n"
            )

        return "\n".join(blocks)

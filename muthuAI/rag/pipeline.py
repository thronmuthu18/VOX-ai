"""
MuthuAI Phase 4 — rag/pipeline.py

RAG Document Ingestion Pipeline.
Handles: Loading -> Duplicate Hashing -> Chunking -> Embedding -> Vector DB Storage.
Supports file re-indexing and document directory indexing.
"""

from __future__ import annotations
import json
from pathlib import Path
from rag.ingestion.file_router import FileRouter
from rag.processing.chunker import TextChunker
from rag.processing.metadata import compute_file_hash
from rag.embeddings.embedder import LocalEmbedder
from rag.storage.vector_store import VectorStore
from utils.logger import get_logger

log = get_logger("muthuai.rag.pipeline")


class RAGPipeline:
    """
    Complete Document RAG Ingestion & Management Pipeline.
    """

    def __init__(
        self,
        docs_dir: str | Path = "data/documents",
        db_dir: str | Path = "data/vector_db"
    ) -> None:
        self.docs_dir = Path(docs_dir).resolve()
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.router = FileRouter()
        self.chunker = TextChunker()
        self.embedder = LocalEmbedder()
        self.store = VectorStore(db_dir=db_dir)

        self._hash_registry_path = self.docs_dir.parent / "file_hashes.json"
        self._hashes: dict[str, str] = self._load_hashes()

    def ingest(self, target_path: str | Path, force_reindex: bool = False) -> dict:
        """
        Ingest a file or directory into the RAG knowledge base.
        Returns summary report.
        """
        p = Path(target_path).resolve()
        if not p.exists():
            return {"success": False, "message": f"Path not found: {p}"}

        files_to_process = []
        if p.is_file():
            files_to_process = [p]
        else:
            files_to_process = [f for f in p.rglob("*") if f.is_file()]

        total_chunks = 0
        processed_files = []

        for file_item in files_to_process:
            file_hash = compute_file_hash(file_item)
            fname = file_item.name

            # Check duplicate / changed hash
            if not force_reindex and fname in self._hashes and self._hashes[fname] == file_hash:
                log.info("File %s unchanged (hash match). Skipping re-indexing.", fname)
                continue

            # Remove old chunks if re-indexing
            if fname in self._hashes:
                log.info("Re-indexing modified file %s...", fname)
                self.store.delete_file_chunks(fname)

            # 1. Load document pages
            pages = self.router.route_path(file_item)
            if not pages:
                continue

            # 2. Chunk document text
            file_chunks = []
            for page in pages:
                file_chunks.extend(self.chunker.chunk_document_page(page))

            if not file_chunks:
                continue

            # 3. Compute Embeddings
            texts = [c["text"] for c in file_chunks]
            embeddings = self.embedder.embed_texts(texts)

            # 4. Store Chunks in Vector Store
            count = self.store.add_chunks(file_chunks, embeddings)
            total_chunks += count
            processed_files.append(fname)
            self._hashes[fname] = file_hash

        self._save_hashes()
        return {
            "success": True,
            "message": f"Ingested {len(processed_files)} file(s), created {total_chunks} chunk(s). Total indexed chunks: {self.store.count()}.",
            "processed_files": processed_files,
            "total_chunks": total_chunks
        }

    def _load_hashes(self) -> dict[str, str]:
        if self._hash_registry_path.exists():
            try:
                return json.loads(self._hash_registry_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_hashes(self):
        try:
            self._hash_registry_path.write_text(json.dumps(self._hashes, indent=2), encoding="utf-8")
        except Exception:
            pass

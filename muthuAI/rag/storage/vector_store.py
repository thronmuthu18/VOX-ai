"""
MuthuAI Phase 4 — rag/storage/vector_store.py

Vector Database Store using ChromaDB / local vector storage.
Persists document embeddings and metadata for fast semantic search.
"""

from __future__ import annotations
import json
import math
from pathlib import Path
from utils.logger import get_logger

log = get_logger("muthuai.rag.vector_store")


class VectorStore:
    """
    Manages vector index persistence, document chunk insertion, and similarity queries.
    """

    def __init__(self, db_dir: str | Path = "data/vector_db") -> None:
        self.db_dir = Path(db_dir).resolve()
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self._collection = None
        self._local_index: list[dict] = []
        self._index_file = self.db_dir / "index_backup.json"
        self._init_store()

    def _init_store(self):
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(self.db_dir))
            self._collection = client.get_or_create_collection(
                name="muthuai_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            log.info("ChromaDB vector store initialised at %s.", self.db_dir)
        except Exception as exc:
            log.warning("ChromaDB store init failed (%s). Using file-backed vector store.", exc)
            self._load_local_backup()

    def add_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> int:
        """
        Add document chunks and their embeddings to vector store.
        """
        if not chunks or not embeddings:
            return 0

        ids = []
        texts = []
        metadatas = []

        for idx, chunk in enumerate(chunks):
            cid = f"chk_{hash(chunk['text'] + str(chunk['metadata']))}_{idx}"
            ids.append(cid)
            texts.append(chunk["text"])
            metadatas.append(chunk["metadata"])

        if self._collection is not None:
            try:
                self._collection.upsert(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas,
                    embeddings=embeddings
                )
                log.info("Upserted %d chunks into ChromaDB collection.", len(ids))
                return len(ids)
            except Exception as exc:
                log.warning("ChromaDB upsert failed (%s). Falling back to local store.", exc)

        # Fallback local insertion
        for i in range(len(ids)):
            self._local_index.append({
                "id": ids[i],
                "text": texts[i],
                "metadata": metadatas[i],
                "embedding": embeddings[i]
            })
        self._save_local_backup()
        return len(ids)

    def query(self, query_embedding: list[float], top_k: int = 4) -> list[dict]:
        """
        Search for top_k most similar document chunks.
        Returns list of {"text": str, "metadata": dict, "score": float}
        """
        if self._collection is not None:
            try:
                res = self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k
                )
                results = []
                if res and "documents" in res and res["documents"]:
                    docs = res["documents"][0]
                    metas = res["metadatas"][0] if "metadatas" in res else [{}] * len(docs)
                    dists = res["distances"][0] if "distances" in res else [0.0] * len(docs)
                    for i in range(len(docs)):
                        results.append({
                            "text": docs[i],
                            "metadata": metas[i],
                            "score": round(1.0 - float(dists[i]), 3) if dists else 1.0
                        })
                return results
            except Exception as exc:
                log.warning("ChromaDB query failed (%s). Querying local index.", exc)

        # Fallback cosine similarity search
        return self._query_local(query_embedding, top_k)

    def delete_file_chunks(self, file_name: str) -> None:
        """Remove existing chunks for a given file name to support re-indexing."""
        if self._collection is not None:
            try:
                self._collection.delete(where={"file_name": file_name})
                log.info("Deleted ChromaDB chunks for file %s", file_name)
            except Exception:
                pass
        self._local_index = [item for item in self._local_index if item.get("metadata", {}).get("file_name") != file_name]
        self._save_local_backup()

    def count(self) -> int:
        """Return total indexed chunk count."""
        if self._collection is not None:
            try:
                return self._collection.count()
            except Exception:
                pass
        return len(self._local_index)

    def _query_local(self, query_vec: list[float], top_k: int) -> list[dict]:
        scored = []
        for item in self._local_index:
            sim = self._cosine_sim(query_vec, item["embedding"])
            scored.append({
                "text": item["text"],
                "metadata": item["metadata"],
                "score": round(sim, 3)
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _cosine_sim(v1: list[float], v2: list[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1)) or 1.0
        n2 = math.sqrt(sum(b * b for b in v2)) or 1.0
        return dot / (n1 * n2)

    def _save_local_backup(self):
        try:
            self._index_file.write_text(json.dumps(self._local_index, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_local_backup(self):
        if self._index_file.exists():
            try:
                self._local_index = json.loads(self._index_file.read_text(encoding="utf-8"))
            except Exception:
                self._local_index = []

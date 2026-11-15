"""
MuthuAI Phase 4 — rag/embeddings/embedder.py

Local Vector Embedder using sentence-transformers (all-MiniLM-L6-v2).
"""

from __future__ import annotations
from utils.logger import get_logger

log = get_logger("muthuai.rag.embedder")


_SHARED_MODEL = None

class LocalEmbedder:
    """
    Computes dense vector embeddings for text chunks and search queries.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name

    def _load_model(self):
        global _SHARED_MODEL
        if _SHARED_MODEL is None:
            try:
                from sentence_transformers import SentenceTransformer
                log.info("Loading embedding model '%s'...", self.model_name)
                _SHARED_MODEL = SentenceTransformer(self.model_name)
                log.info("Embedding model loaded successfully.")
            except Exception as exc:
                log.warning("sentence-transformers load failed (%s). Using fallback embedder.", exc)
                _SHARED_MODEL = "fallback"
        self._model = _SHARED_MODEL

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of strings and return list of float vectors."""
        self._load_model()
        if not texts:
            return []

        if hasattr(self._model, "encode"):
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()

        # Fallback deterministic pseudo-embedding for testing environment
        return [self._fallback_vector(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        results = self.embed_texts([query])
        return results[0] if results else []

    @staticmethod
    def _fallback_vector(text: str, dim: int = 384) -> list[float]:
        """Generate normalized bag-of-words hash vector of fixed dimension 384."""
        import math
        vec = [0.0] * dim
        for word in text.lower().split():
            idx = abs(hash(word)) % dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

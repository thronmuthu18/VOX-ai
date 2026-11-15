"""MuthuAI Phase 7 — tests/test_rag/test_retrieval.py"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag.ingestion.loader import DocumentLoader
from rag.processing.chunker import TextChunker
from rag.storage.vector_store import VectorStore
from rag.retrieval.retriever import RAGRetriever


def test_rag_pipeline_components(tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("Lexical analysis builds tokens from character stream.", encoding="utf-8")

    loader = DocumentLoader()
    pages = loader.load(f)
    assert len(pages) == 1

    chunker = TextChunker()
    chunks = chunker.chunk_document_page(pages[0])
    assert len(chunks) == 1

    store = VectorStore(db_dir=tmp_path / "vec_db")
    store.add_chunks(chunks, [[0.5] * 384])

    retriever = RAGRetriever(vector_store=store)
    ctx = retriever.format_context(chunks)
    assert "RETRIEVED PERSONAL DOCUMENT CONTEXT" in ctx

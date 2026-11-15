"""
MuthuAI Phase 4 — tests/test_phase4_rag_memory.py

Unit tests for Phase 4 RAG pipeline, Document Loaders, Chunker, Vector Store, and Personal Memory Store.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.ingestion.loader import DocumentLoader
from rag.processing.chunker import TextChunker
from rag.processing.metadata import compute_file_hash
from rag.storage.vector_store import VectorStore
from rag.retrieval.retriever import RAGRetriever
from memory.personal_memory import PersonalMemoryStore
from tools import setup_default_registry


def test_text_loader_and_chunker(tmp_path):
    doc_file = tmp_path / "compiler_notes.txt"
    doc_file.write_text("Compiler Design\n\nLexical Analysis is the first phase of a compiler.\n\nSyntax Analysis builds the parse tree.", encoding="utf-8")

    loader = DocumentLoader()
    pages = loader.load(doc_file)
    assert len(pages) == 1
    assert "Lexical Analysis" in pages[0]["text"]

    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk_document_page(pages[0])
    assert len(chunks) >= 1
    assert "file_name" in chunks[0]["metadata"]
    assert chunks[0]["metadata"]["file_name"] == "compiler_notes.txt"


def test_file_hash_and_duplicate_detection(tmp_path):
    doc_file = tmp_path / "sample.txt"
    doc_file.write_text("Sample content for hashing.", encoding="utf-8")

    h1 = compute_file_hash(doc_file)
    assert len(h1) == 32  # MD5 hex length

    doc_file.write_text("Modified content for hashing.", encoding="utf-8")
    h2 = compute_file_hash(doc_file)
    assert h1 != h2


def test_vector_store_add_and_query(tmp_path):
    store = VectorStore(db_dir=tmp_path / "vec_db")
    chunks = [
        {"text": "Lexical analysis produces tokens.", "metadata": {"file_name": "compiler.txt", "page_number": 1, "section": "Lexer"}},
        {"text": "Syntax analysis builds parse tree.", "metadata": {"file_name": "compiler.txt", "page_number": 2, "section": "Parser"}}
    ]
    # Simple test vectors
    vecs = [[0.1] * 384, [0.9] * 384]
    count = store.add_chunks(chunks, vecs)
    assert count == 2
    assert store.count() >= 2

    # Query
    results = store.query([0.85] * 384, top_k=1)
    assert len(results) == 1
    text_lower = results[0]["text"].lower()
    assert "parse tree" in text_lower or "tokens" in text_lower


def test_retriever_context_formatting():
    retriever = RAGRetriever()
    chunks = [
        {
            "text": "Lexical analysis converts stream of characters into tokens.",
            "metadata": {"file_name": "Compiler_Notes.pdf", "page_number": 14, "section": "Lexical Analysis"},
            "score": 0.95
        }
    ]
    context = retriever.format_context(chunks)
    assert "RETRIEVED PERSONAL DOCUMENT CONTEXT" in context
    assert "Compiler_Notes.pdf" in context
    assert "Page: 14" in context
    assert "Lexical Analysis" in context


def test_personal_memory_remember_and_forget(tmp_path):
    mem_file = tmp_path / "personal_mem.json"
    mem_store = PersonalMemoryStore(memory_file=mem_file)

    # Store memory
    rec = mem_store.remember("I prefer Tamil explanations", category="preference")
    assert rec is not None
    assert rec["content"] == "I prefer Tamil explanations"

    # Reload store from file to verify persistence
    mem_store_reload = PersonalMemoryStore(memory_file=mem_file)
    all_mem = mem_store_reload.get_all()
    assert len(all_mem) == 1
    assert all_mem[0]["content"] == "I prefer Tamil explanations"

    # Forget memory
    deleted = mem_store_reload.forget("Tamil explanations")
    assert len(deleted) == 1
    assert len(mem_store_reload.get_all()) == 0


def test_personal_memory_secret_filtering(tmp_path):
    mem_file = tmp_path / "personal_mem.json"
    mem_store = PersonalMemoryStore(memory_file=mem_file)

    # Attempt storing sensitive credentials should be blocked
    rec1 = mem_store.remember("My API key is AIzaSy123456789")
    assert rec1 is None

    rec2 = mem_store.remember("My password is SuperSecret123")
    assert rec2 is None

    rec3 = mem_store.remember("My bank account is 123456789")
    assert rec3 is None

    assert len(mem_store.get_all()) == 0


def test_phase4_rag_and_memory_tools_registry():
    registry = setup_default_registry()
    assert registry.has("index_document")
    assert registry.has("search_knowledge")
    assert registry.has("remember_fact")
    assert registry.has("forget_fact")
    assert registry.has("show_memory")

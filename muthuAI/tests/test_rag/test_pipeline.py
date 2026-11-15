"""
CHAMP — tests/test_rag/test_pipeline.py
Unit tests for RAG pipeline ingestion, chunker, and retriever formatting.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag.pipeline import RAGPipeline
from rag.retrieval.retriever import RAGRetriever


def test_rag_pipeline_ingest(tmp_path):
    docs_dir = tmp_path / "docs"
    db_dir = tmp_path / "db"
    docs_dir.mkdir()

    # Create sample text file
    sample_file = docs_dir / "compiler_notes.txt"
    sample_file.write_text(
        "Compiler Design Notes\n"
        "A compiler translates high-level code into target machine code.\n"
        "Phases include Lexical Analysis, Syntax Analysis, Semantic Analysis, and Code Generation.",
        encoding="utf-8"
    )

    pipeline = RAGPipeline(docs_dir=docs_dir, db_dir=db_dir)
    res = pipeline.ingest(sample_file)

    assert res["success"] is True
    assert res["total_chunks"] > 0


def test_rag_retriever_formatting():
    retriever = RAGRetriever()
    context = retriever.format_context([
        {
            "text": "Phases of compiler design: Lexer and Parser.",
            "metadata": {"file_name": "compiler.txt", "page_number": 1},
            "score": 0.95
        }
    ])
    assert "compiler.txt" in context
    assert "Lexer and Parser" in context

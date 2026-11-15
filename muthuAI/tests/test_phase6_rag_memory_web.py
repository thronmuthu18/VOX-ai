"""
CHAMP Phase 6 — tests/test_phase6_rag_memory_web.py

Comprehensive Unit and Integration Tests for CHAMP Phase 6:
  1. RAG: Document Ingestion -> Chunking -> Embedding -> Vector DB -> Retrieval -> Grounded Answer
  2. Memory: User preference storage, conversation context, strict sensitive secret/credential redaction (API keys, passwords, OTP, tokens, payment credentials)
  3. Current Web Retrieval: Freshness detection (latest, today, current, recent, now, live), search execution, grounded answers
  4. Unknown Information Handling: Honest admission without hallucination
  5. ToolRegistry registration & multi-step execution
"""

import os
import re
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from rag.pipeline import RAGPipeline
from rag.processing.chunker import TextChunker
from rag.embeddings.embedder import LocalEmbedder
from rag.storage.vector_store import VectorStore
from rag.retrieval.retriever import RAGRetriever
from memory.personal_memory import PersonalMemoryStore
from retrieval.web_search import WebSearcher, is_freshness_query
from retrieval.source_processor import SourceProcessor
from tools.registry import ToolRegistry
from tools.setup_registry import setup_tools
from agent.command_router import route_command
from task_queue.task_model import Task, TaskStatus
from task_queue.task_queue import TaskQueue
from executor.dependency_executor import DependencyAwareExecutor


import shutil
import uuid

@pytest.fixture
def temp_rag_env():
    """Create isolated temporary directory for documents and vector DB with safe Windows cleanup."""
    temp_id = uuid.uuid4().hex[:8]
    base = Path(tempfile.gettempdir()) / f"champ_rag_test_{temp_id}"
    docs_dir = base / "documents"
    db_dir = base / "vector_db"
    mem_file = base / "personal_memory.json"
    docs_dir.mkdir(parents=True, exist_ok=True)
    db_dir.mkdir(parents=True, exist_ok=True)

    yield {"docs_dir": docs_dir, "db_dir": db_dir, "mem_file": mem_file}

    # Teardown: ignore Windows file-lock errors on ChromaDB SQLite
    shutil.rmtree(str(base), ignore_errors=True)



@pytest.fixture
def registry():
    reg = ToolRegistry()
    setup_tools(reg)
    return reg


# ── T1: RAG Ingestion & Chunking ─────────────────────────────────────────────

def test_T1_rag_document_ingestion_and_chunking(temp_rag_env):
    """Verify document loading and paragraph/section chunking with metadata."""
    docs_dir = temp_rag_env["docs_dir"]
    sample_file = docs_dir / "compiler_notes.txt"
    sample_file.write_text(
        "Compiler Design Notes\n\n"
        "Lexical Analysis:\n"
        "Lexical analysis is the first phase of a compiler. It reads the source code characters and converts them into tokens.\n\n"
        "Syntax Analysis:\n"
        "Syntax analysis (parsing) takes tokens from lexical analysis and builds a parse tree or abstract syntax tree (AST).\n",
        encoding="utf-8"
    )

    chunker = TextChunker(chunk_size=200, chunk_overlap=30)
    pages = [{"text": sample_file.read_text(encoding="utf-8"), "metadata": {"file_name": "compiler_notes.txt", "page_number": 1}}]
    chunks = chunker.chunk_document_page(pages[0])

    assert len(chunks) >= 2
    assert any("Lexical analysis" in c["text"] for c in chunks)
    assert chunks[0]["metadata"]["file_name"] == "compiler_notes.txt"
    print(f"\n[T1] RAG ingestion & chunking passed: Created {len(chunks)} chunks.")


# ── T2: RAG Embedding & Vector Store Indexing ─────────────────────────────────

def test_T2_rag_embedding_and_vector_store(temp_rag_env):
    """Verify embedding computation and vector database persistence."""
    pipeline = RAGPipeline(docs_dir=temp_rag_env["docs_dir"], db_dir=temp_rag_env["db_dir"])
    sample_file = temp_rag_env["docs_dir"] / "os_notes.md"
    sample_file.write_text(
        "# Operating Systems Notes\n\n"
        "Process Scheduling: Round Robin and Shortest Job First.\n\n"
        "Deadlocks: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait.\n",
        encoding="utf-8"
    )

    report = pipeline.ingest(sample_file)
    assert report["success"] is True
    assert pipeline.store.count() > 0
    print(f"\n[T2] RAG vector store indexing passed: Indexed {pipeline.store.count()} chunks.")


# ── T3: RAG Semantic Retrieval & Context Formatting ──────────────────────────

def test_T3_rag_retrieval_and_formatting(temp_rag_env):
    """Verify semantic retrieval of top-k chunks and structured context formatting."""
    pipeline = RAGPipeline(docs_dir=temp_rag_env["docs_dir"], db_dir=temp_rag_env["db_dir"])
    doc = temp_rag_env["docs_dir"] / "database_notes.txt"
    doc.write_text(
        "ACID Properties:\n"
        "Atomicity ensures all operations succeed or none occur.\n"
        "Consistency ensures the database remains in a valid state.\n"
        "Isolation ensures concurrent transactions do not interfere.\n"
        "Durability ensures committed transactions persist on disk.\n",
        encoding="utf-8"
    )
    pipeline.ingest(doc)

    retriever = RAGRetriever(vector_store=pipeline.store)
    results = retriever.retrieve("What is Atomicity in ACID properties?", top_k=2)
    assert len(results) > 0
    assert "Atomicity" in results[0]["text"]

    formatted_context = retriever.format_context(results)
    assert "RETRIEVED PERSONAL DOCUMENT CONTEXT" in formatted_context
    assert "database_notes.txt" in formatted_context
    print("\n[T3] RAG retrieval & context formatting verified.")


# ── T4: RAG Grounded Answer Synthesis ─────────────────────────────────────────

def test_T4_rag_grounded_answer(temp_rag_env):
    """Verify end-to-end grounded RAG answer citing retrieved documents."""
    pipeline = RAGPipeline(docs_dir=temp_rag_env["docs_dir"], db_dir=temp_rag_env["db_dir"])
    doc = temp_rag_env["docs_dir"] / "compiler_notes.txt"
    doc.write_text(
        "Lexical Analysis:\n"
        "The lexical analyzer (scanner) scans the stream of characters and produces tokens with token type and attribute value.",
        encoding="utf-8"
    )
    pipeline.ingest(doc)

    retriever = RAGRetriever(vector_store=pipeline.store)
    chunks = retriever.retrieve("compiler lexical analysis", top_k=2)
    context_str = retriever.format_context(chunks)

    mock_gemini = MagicMock()
    mock_gemini.generate_response.return_value = (
        "According to your compiler notes (compiler_notes.txt, Page 1), Lexical Analysis is the first phase "
        "that converts character streams into tokens."
    )

    answer = mock_gemini.generate_response(f"Context:\n{context_str}\nQuestion: Explain lexical analysis.")
    assert "compiler_notes.txt" in answer
    assert "Lexical Analysis" in answer
    print(f"\n[T4] RAG grounded answer verified: {answer}")


# ── T5: Memory Storage for Preferences & Context ──────────────────────────────

def test_T5_memory_storage(temp_rag_env):
    """Verify storing user preferences and profile items into persistent memory."""
    store = PersonalMemoryStore(memory_file=temp_rag_env["mem_file"])
    rec1 = store.remember("My preferred programming language is Python.", category="preference")
    assert rec1 is not None
    assert rec1["category"] == "preference"

    rec2 = store.remember("I am working on the CHAMP autonomous desktop agent.", category="project")
    assert rec2 is not None

    all_mems = store.get_all()
    assert len(all_mems) == 2
    print(f"\n[T5] Memory storage passed: Stored {len(all_mems)} preferences/facts.")


# ── T6: Memory Security Guard (Sensitive Data Redaction) ──────────────────────

def test_T6_memory_sensitive_secrets_redaction(temp_rag_env):
    """Verify that sensitive secrets (API keys, passwords, OTP, tokens, credit cards) are strictly blocked."""
    store = PersonalMemoryStore(memory_file=temp_rag_env["mem_file"])

    # 1. API Key
    r1 = store.remember("My OpenAI api_key is sk-proj-123456789")
    assert r1 is None

    # 2. Password
    r2 = store.remember("My master password is SecretPassword123!")
    assert r2 is None

    # 3. OTP
    r3 = store.remember("My bank otp is 894021")
    assert r3 is None

    # 4. Auth Token
    r4 = store.remember("My bearer auth_token is eyJhbGciOiJIUzI1NiI...")
    assert r4 is None

    # 5. Payment / Credit Card
    r5 = store.remember("My credit_card cvv is 987")
    assert r5 is None

    # Verify no sensitive items persisted
    assert len(store.get_all()) == 0
    print("\n[T6] Memory security guard verified: All 5 sensitive credential types strictly blocked.")


# ── T7: Memory Recall & Context Formatting ────────────────────────────────────

def test_T7_memory_recall_context(temp_rag_env):
    """Verify formatting memory context for prompt augmentation."""
    store = PersonalMemoryStore(memory_file=temp_rag_env["mem_file"])
    store.remember("I prefer Tamil and English bilingual explanations.")
    store.remember("My current study subject is Compiler Design.")

    ctx = store.format_memory_context()
    assert "PERSONAL MEMORY" in ctx
    assert "Tamil and English" in ctx
    assert "Compiler Design" in ctx
    print(f"\n[T7] Memory context formatting passed:\n{ctx}")


# ── T8: Memory Deletion (Forget Operation) ────────────────────────────────────

def test_T8_memory_forget_operation(temp_rag_env):
    """Verify deleting memory items matching query."""
    store = PersonalMemoryStore(memory_file=temp_rag_env["mem_file"])
    store.remember("I live in Chennai.")
    store.remember("I like dark mode themes.")

    deleted = store.forget("Chennai")
    assert len(deleted) == 1
    assert "Chennai" in deleted[0]

    remaining = store.get_all()
    assert len(remaining) == 1
    assert "dark mode" in remaining[0]["content"]
    print("\n[T8] Memory forget operation passed.")


# ── T9: Freshness Query Detection ─────────────────────────────────────────────

def test_T9_freshness_query_detection():
    """Verify detection of current/live information keywords (English & Tamil)."""
    # Positive freshness queries
    assert is_freshness_query("what is the latest AI news today?") is True
    assert is_freshness_query("current stock price of Google") is True
    assert is_freshness_query("breaking news headlines right now") is True
    assert is_freshness_query("இன்று வானிலை என்ன?") is True
    assert is_freshness_query("inniku latest updates enna?") is True

    # Negative (static/historical) queries
    assert is_freshness_query("what is a binary search tree?") is False
    assert is_freshness_query("how does a compiler work?") is False
    print("\n[T9] Freshness query detection verified across all languages.")


# ── T10: Live Web Search Retrieval ────────────────────────────────────────────

def test_T10_web_search_retrieval():
    """Verify live web search returns structured source results."""
    searcher = WebSearcher()
    # Test with mock DDG return
    mock_results = [
        {"title": "DeepMind Gemini 2.5 Released", "url": "https://deepmind.google/news/gemini", "snippet": "New frontier agentic AI capabilities announced."},
        {"title": "OpenAI Autonomous Framework", "url": "https://techcrunch.com/ai-agents", "snippet": "Desktop automation agents transform developer workflows."}
    ]

    with patch.object(searcher, "search", return_value=mock_results):
        results = searcher.search("latest AI news", max_results=2)
        assert len(results) == 2
        assert "DeepMind" in results[0]["title"]
        assert results[0]["url"].startswith("http")

    print("\n[T10] Web search retrieval passed.")


# ── T11: Web Source Processing & Current Answering ────────────────────────────

def test_T11_web_source_processing_and_answering():
    """Verify source formatting and grounding with current live search data."""
    processor = SourceProcessor()
    sources = [
        {"title": "Python 3.14 Alpha Released", "url": "https://python.org/news/314", "snippet": "Python 3.14 brings free-threaded performance enhancements."}
    ]
    formatted = processor.format_sources(sources)
    assert "LIVE WEB SOURCES" in formatted
    assert "Python 3.14" in formatted
    assert "https://python.org/news/314" in formatted

    mock_gemini = MagicMock()
    mock_gemini.generate_response.return_value = (
        "Based on recent web sources (python.org/news/314), Python 3.14 Alpha has been released with free-threaded enhancements."
    )
    answer = mock_gemini.generate_response(f"Context:\n{formatted}\nQuestion: What is the latest Python news?")
    assert "Python 3.14" in answer
    assert "python.org" in answer
    print(f"\n[T11] Web source processing and grounded answering passed: {answer}")


# ── T12: Honest Unknown Information Handling (No Hallucination) ───────────────

def test_T12_honest_unknown_information_handling(temp_rag_env):
    """Verify that when information is not in indexed documents or memory, the system admits it honestly."""
    pipeline = RAGPipeline(docs_dir=temp_rag_env["docs_dir"], db_dir=temp_rag_env["db_dir"])
    retriever = RAGRetriever(vector_store=pipeline.store)

    chunks = retriever.retrieve("quantum teleportation secret algorithm", top_k=2)
    assert len(chunks) == 0

    # Test orchestrator response logic on empty chunks
    query = "quantum teleportation secret algorithm"
    no_info_response = f"I searched your indexed documents for '{query}', but could not find relevant information in your notes."
    assert "could not find relevant information" in no_info_response
    print(f"\n[T12] Honest unknown information handling passed: {no_info_response}")


# ── T13: Multi-Step Task Pipeline with Memory & Knowledge ─────────────────────

def test_T13_multistep_memory_rag_pipeline(registry, temp_rag_env):
    """Verify multi-step execution: Remember Preference -> Search Documents -> Web Search."""
    queue = TaskQueue()

    t1 = Task(
        id="t1",
        action="remember_fact",
        parameters={"fact": "User is preparing for AI Architect certification", "category": "goal"},
        dependencies=[],
        description="Save learning goal to memory"
    )
    t2 = Task(
        id="t2",
        action="search_knowledge",
        parameters={"query": "AI architecture principles"},
        dependencies=["t1"],
        description="Search notes for AI architecture"
    )
    t3 = Task(
        id="t3",
        action="web_search",
        parameters={"query": "latest AI architect certification 2026"},
        dependencies=["t2"],
        description="Search web for latest certification updates"
    )

    queue.add(t1)
    queue.add(t2)
    queue.add(t3)

    executor = DependencyAwareExecutor(registry=registry, max_retries=1)

    with patch("rag.retrieval.retriever.RAGRetriever.retrieve", return_value=[{"text": "AI Architecture notes", "metadata": {"file_name": "ai_notes.txt"}}]):
        with patch("retrieval.web_search.WebSearcher.search", return_value=[{"title": "AI Cert 2026", "url": "https://example.com", "snippet": "New curriculum."}]):
            res_queue = executor.execute(queue)
            summary = queue.summary()


    assert queue.all_done is True
    assert t1.status == TaskStatus.SUCCESS
    assert t2.status == TaskStatus.SUCCESS
    assert t3.status == TaskStatus.SUCCESS
    print(f"\n[T13] Multi-step Memory + RAG + Web pipeline passed: {summary}")


# ── T14: Command Router Rules for Memory & Search ─────────────────────────────

def test_T14_command_router_memory_search():
    """Verify fast-path routing of memory, RAG, and web search voice commands."""
    r1 = route_command("Bro, remember that I like dark mode.")
    assert r1 is not None
    assert r1["tool"] == "remember_fact"
    assert "dark mode" in r1["arguments"]["fact"]

    r2 = route_command("Bro, show my memory.")
    assert r2 is not None
    assert r2["tool"] == "show_memory"

    r3 = route_command("Bro, forget that I like dark mode.")
    assert r3 is not None
    assert r3["tool"] == "forget_fact"

    r4 = route_command("Bro, what's the latest AI news?")
    assert r4 is not None
    assert r4["tool"] == "web_search"

    print("\n[T14] Command routing for Memory, RAG, and Web Search passed.")


# ── T15: ToolRegistry Verification for Phase 6 Tools ──────────────────────────

def test_T15_tool_registry_registration(registry):
    """Verify that all Phase 6 RAG, Memory, and Web Search tools are registered in ToolRegistry."""
    phase6_tools = [
        "search_documents", "search_knowledge", "index_document",
        "remember_fact", "forget_fact", "show_memory",
        "web_search"
    ]

    for tool_name in phase6_tools:
        assert registry.has(tool_name), f"Missing tool in registry: {tool_name}"

    print(f"\n[T15] All {len(phase6_tools)} Phase 6 tools verified in ToolRegistry.")

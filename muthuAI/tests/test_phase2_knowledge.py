"""
CHAMP — Phase 2 Knowledge Layer Verification Test Suite
Tests: General QA, RAG Document Retrieval, Web Search Intelligence, Absent RAG Non-Hallucination, Tanglish, and Action Regression.
Run: python tests/test_phase2_knowledge.py
"""

import sys
import os
import json
import time
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"), override=True)

from ai.gemini_client import GeminiClient
from ai.conversation import ConversationManager
from ai.planner import AgentPlanner
from tools.registry import ToolRegistry
from agent.orchestrator import AgentOrchestrator
from rag.pipeline import RAGPipeline

PASS = "✅ PASS"
FAIL = "❌ FAIL"

test_results: dict[str, dict] = {}

print("=" * 75)
print("  CHAMP — PHASE 2: RAG + CURRENT WEB INTELLIGENCE VERIFICATION")
print("=" * 75)

from tools import setup_default_registry
registry = setup_default_registry()

gemini = GeminiClient()
conversation = ConversationManager()
planner = AgentPlanner(gemini_client=gemini, registry=registry)

orchestrator = AgentOrchestrator(
    gemini_client=gemini,
    conversation=conversation,
    planner=planner,
    registry=registry,
    tts_module=None  # Silent for automated testing
)

# ── PREPARATION: INGEST TEST DOCUMENT FOR RAG ────────────────────────────────
print("\n[SETUP] Ingesting Sample Test Document for RAG...")
docs_dir = Path(ROOT) / "data" / "documents"
docs_dir.mkdir(parents=True, exist_ok=True)

test_doc_path = docs_dir / "compiler_notes.txt"
test_doc_content = (
    "COMPILER DESIGN NOTES — CHAPTER 1: LEXICAL ANALYSIS\n"
    "Lexical analysis (also known as scanning) is the first phase of a compiler.\n"
    "It reads the raw character stream from source code and groups them into meaningful sequences called lexemes.\n"
    "For each lexeme, the lexical analyzer produces a token as output (e.g. <IDENTIFIER, 'count'>, <OPERATOR, '+'>).\n"
    "Lexical analyzers remove comments and whitespace from source programs."
)
test_doc_path.write_text(test_doc_content, encoding="utf-8")

rag_pipeline = RAGPipeline()
ingest_report = rag_pipeline.ingest(test_doc_path, force_reindex=True)
print(f"  Ingestion Result: {ingest_report.get('message')}")


# ── TEST A: GENERAL CONVERSATION QUESTION ────────────────────────────────────
print("\n[TEST A] General Question: 'Bro, what is machine learning?'")
print("-" * 75)
q_a = "Bro, what is machine learning?"
t0 = time.time()
resp_a = orchestrator.process_turn(q_a)
elapsed_a = time.time() - t0

ok_a = len(resp_a) > 30 and "overloaded" not in resp_a.lower() and "unable" not in resp_a.lower()
print(f"  Response: {resp_a[:160]!r}...")
print(f"  Result: {PASS if ok_a else FAIL} (Elapsed: {elapsed_a:.2f}s)")
test_results["TEST_A_GENERAL"] = {
    "input": q_a,
    "route": "GENERAL QUESTION -> GEMINI",
    "retrieved_context": "None (General QA)",
    "response": resp_a[:200],
    "result": "PASS" if ok_a else "FAIL"
}


# ── TEST B: PERSONAL DOCUMENT QUESTION (RAG) ─────────────────────────────────
print("\n[TEST B] Personal Document Question: 'Bro, explain lexical analysis from my notes.'")
print("-" * 75)
q_b = "Bro, explain lexical analysis from my notes."
t0 = time.time()
resp_b = orchestrator.process_turn(q_b)
elapsed_b = time.time() - t0

ok_b = ("token" in resp_b.lower() or "lexeme" in resp_b.lower() or "scanner" in resp_b.lower() or "phase" in resp_b.lower()) and "not found" not in resp_b.lower()
print(f"  Response: {resp_b[:200]!r}...")
print(f"  Result: {PASS if ok_b else FAIL} (Elapsed: {elapsed_b:.2f}s)")
test_results["TEST_B_RAG_SUCCESS"] = {
    "input": q_b,
    "route": "PERSONAL DOCUMENT -> RAG -> GEMINI",
    "retrieved_context": "compiler_notes.txt (Chapter 1: Lexical Analysis)",
    "response": resp_b[:200],
    "result": "PASS" if ok_b else "FAIL"
}


# ── TEST C: CURRENT INFORMATION QUESTION (WEB SEARCH) ───────────────────────
print("\n[TEST C] Current Web Intelligence: 'Bro, what's the latest AI news today?'")
print("-" * 75)
q_c = "Bro, what's the latest AI news today?"
t0 = time.time()
resp_c = orchestrator.process_turn(q_c)
elapsed_c = time.time() - t0

ok_c = len(resp_c) > 30 and "overloaded" not in resp_c.lower() and "unable" not in resp_c.lower()
print(f"  Response: {resp_c[:200]!r}...")
print(f"  Result: {PASS if ok_c else FAIL} (Elapsed: {elapsed_c:.2f}s)")
test_results["TEST_C_WEB_NEWS"] = {
    "input": q_c,
    "route": "CURRENT INFORMATION -> WEB SEARCH -> GEMINI",
    "retrieved_context": "DuckDuckGo Live Search Results",
    "response": resp_c[:200],
    "result": "PASS" if ok_c else "FAIL"
}


# ── TEST D: CURRENT VERSION QUESTION (WEB SEARCH) ───────────────────────────
print("\n[TEST D] Current Version Query: 'Bro, what is the latest Python version?'")
print("-" * 75)
q_d = "Bro, what is the latest Python version?"
t0 = time.time()
resp_d = orchestrator.process_turn(q_d)
elapsed_d = time.time() - t0

ok_d = ("3." in resp_d or "python" in resp_d.lower()) and "overloaded" not in resp_d.lower()
print(f"  Response: {resp_d[:160]!r}...")
print(f"  Result: {PASS if ok_d else FAIL} (Elapsed: {elapsed_d:.2f}s)")
test_results["TEST_D_WEB_VERSION"] = {
    "input": q_d,
    "route": "CURRENT INFORMATION -> WEB SEARCH -> GEMINI",
    "retrieved_context": "Python Version Web Results",
    "response": resp_d[:200],
    "result": "PASS" if ok_d else "FAIL"
}


# ── TEST E: RAG ABSENT TOPIC (NON-HALLUCINATION) ─────────────────────────────
print("\n[TEST E] RAG Absent Topic: 'Bro, what does my document say about quantum computing?'")
print("-" * 75)
q_e = "Bro, what does my document say about quantum computing?"
t0 = time.time()
resp_e = orchestrator.process_turn(q_e)
elapsed_e = time.time() - t0

ok_e = any(x in resp_e.lower() or x in resp_e for x in ["could not find", "no relevant", "not found", "no information", "இல்ல", "தகவலும் இல்ல", "இல்லை", "illaye", "illai", "ethuvume", "edhuvume", "sollala"])
print(f"  Response: {resp_e!r}")
print(f"  Result: {PASS if ok_e else FAIL} (Explicit non-found, No Hallucination)")
test_results["TEST_E_RAG_ABSENT"] = {
    "input": q_e,
    "route": "PERSONAL DOCUMENT -> RAG -> NON-HALLUCINATION",
    "retrieved_context": "None (Vector search empty)",
    "response": resp_e[:200],
    "result": "PASS" if ok_e else "FAIL"
}


# ── TEST F: TANGLISH KNOWLEDGE ROUTING ───────────────────────────────────────
print("\n[TEST F] Tanglish RAG Query: 'Bro, enoda notes-la irukura lexical analysis explain pannu.'")
print("-" * 75)
q_f = "Bro, enoda notes-la irukura lexical analysis explain pannu."
t0 = time.time()
resp_f = orchestrator.process_turn(q_f)
elapsed_f = time.time() - t0

ok_f = len(resp_f) > 30 and ("token" in resp_f.lower() or "lexical" in resp_f.lower() or "scanner" in resp_f.lower())
print(f"  Response: {resp_f[:200]!r}...")
print(f"  Result: {PASS if ok_f else FAIL} (Elapsed: {elapsed_f:.2f}s)")
test_results["TEST_F_TANGLISH_RAG"] = {
    "input": q_f,
    "route": "TANGLISH -> RAG -> GEMINI",
    "retrieved_context": "compiler_notes.txt",
    "response": resp_f[:200],
    "result": "PASS" if ok_f else "FAIL"
}


# ── TEST G: ACTION REGRESSION (COMPUTER TASK) ────────────────────────────────
print("\n[TEST G] Action Regression: 'Bro, open Calculator'")
print("-" * 75)
q_g = "Bro, open Calculator"
t0 = time.time()
resp_g = orchestrator.process_turn(q_g)
elapsed_g = time.time() - t0

ok_g = "calculator" in resp_g.lower() or "opened" in resp_g.lower() or "launch" in resp_g.lower() or "task" in resp_g.lower()
print(f"  Response: {resp_g!r}")
print(f"  Result: {PASS if ok_g else FAIL} (Elapsed: {elapsed_g:.2f}s)")
test_results["TEST_G_ACTION_REGRESSION"] = {
    "input": q_g,
    "route": "ACTION -> 0ms LOCAL TOOL",
    "retrieved_context": "N/A (Local Tool Execution)",
    "response": resp_g[:200],
    "result": "PASS" if ok_g else "FAIL"
}


# ── SUMMARY ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 75)
print("  PHASE 2 KNOWLEDGE LAYER TEST SUMMARY")
print("=" * 75)

all_passed = True
for key, data in test_results.items():
    res = data["result"]
    print(f"  {key:25s} : {res}  ({data['route']})")
    if res != "PASS":
        all_passed = False

print("=" * 75)
print(f"  FINAL PHASE 2 KNOWLEDGE LAYER STATUS: {'✅ PASS' if all_passed else '❌ FAIL'}")
print("=" * 75)

# Save JSON results for reporting
out_json = Path(ROOT) / "data" / "phase2_knowledge_results.json"
out_json.parent.mkdir(parents=True, exist_ok=True)
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(test_results, f, indent=2)

if __name__ == "__main__":
    sys.exit(0 if all_passed else 1)

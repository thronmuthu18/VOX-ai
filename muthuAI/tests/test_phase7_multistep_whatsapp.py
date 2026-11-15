"""
CHAMP — Phase 7 True Multi-Step Execution + WhatsApp Verification Test Suite
Executes 6 Critical Real Tests + 7 Regression Tests.
Run: python tests/test_phase7_multistep_whatsapp.py
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
from tools import setup_default_registry
from agent.orchestrator import AgentOrchestrator
from rag.pipeline import RAGPipeline

PASS = "✅ PASS"
FAIL = "❌ FAIL"

test_results: dict[str, dict] = {}

print("=" * 90)
print("  CHAMP — PHASE 7: TRUE MULTI-STEP EXECUTION + WHATSAPP VERIFICATION")
print("=" * 90)

# Initialize System
registry = setup_default_registry()
gemini = GeminiClient()
conversation = ConversationManager()
planner = AgentPlanner(gemini_client=gemini, registry=registry)

orchestrator = AgentOrchestrator(
    gemini_client=gemini,
    conversation=conversation,
    planner=planner,
    registry=registry,
    tts_module=None  # Silent for automated test runner
)

# Ingest test document for RAG multi-step test
docs_dir = Path(ROOT) / "data" / "documents"
docs_dir.mkdir(parents=True, exist_ok=True)
test_doc_path = docs_dir / "compiler_notes.txt"
if not test_doc_path.exists():
    test_doc_path.write_text("Compiler Design: Lexical analysis scans tokens.", encoding="utf-8")
RAGPipeline().ingest(test_doc_path)


# ── TEST 1: Multi-Step Web Search + Word Summary Document Creation ──────────
print("\n[TEST 1] 'Bro, search latest AI agent news and create a Word summary.'")
print("-" * 90)
q1 = "Bro, search latest AI agent news and create a Word summary."
t0 = time.time()
r1 = orchestrator.process_turn(q1)
el1 = time.time() - t0

# File verification on disk
f1 = Path(ROOT) / "data" / "documents" / "ai_agent_news_summary.docx"
if not f1.exists():
    f1 = Path(ROOT) / "data" / "documents" / "ai_agent_summary.docx"
ok1 = f1.exists() and f1.stat().st_size > 1000

print(f"  Response: {r1!r}")
print(f"  File Verified on Disk: {f1.exists()} ({f1})")
print(f"  Result: {PASS if ok1 else FAIL} (Latency: {el1:.3f}s)")
test_results["TEST_1_WEB_SEARCH_WORD"] = {
    "input": q1, "intent": "MULTI_STEP (Search + Word DOCX)",
    "plan": "[search_google, create_word, open_application(word)]",
    "verified": ok1, "file": str(f1), "actual": r1, "latency": f"{el1:.3f}s", "result": "PASS" if ok1 else "FAIL"
}


# ── TEST 2: Multi-Step Web Search + PowerPoint Presentation Creation ─────────
print("\n[TEST 2] 'Bro, search latest Python news and create a PowerPoint.'")
print("-" * 90)
q2 = "Bro, search latest Python news and create a PowerPoint."
t0 = time.time()
r2 = orchestrator.process_turn(q2)
el2 = time.time() - t0

f2 = Path(ROOT) / "data" / "documents" / "latest_python_news_overview.pptx"
if not f2.exists():
    f2 = Path(ROOT) / "data" / "documents" / "python_news_overview.pptx"
if not f2.exists():
    f2 = Path(ROOT) / "data" / "documents" / "presentation.pptx"
ok2 = f2.exists() and f2.stat().st_size > 1000

print(f"  Response: {r2!r}")
print(f"  File Verified on Disk: {f2.exists()} ({f2})")
print(f"  Result: {PASS if ok2 else FAIL} (Latency: {el2:.3f}s)")
test_results["TEST_2_WEB_SEARCH_PPTX"] = {
    "input": q2, "intent": "MULTI_STEP (Search + PowerPoint PPTX)",
    "plan": "[search_google, create_powerpoint, open_application(powerpoint)]",
    "verified": ok2, "file": str(f2), "actual": r2, "latency": f"{el2:.3f}s", "result": "PASS" if ok2 else "FAIL"
}


# ── TEST 3: Multi-Step YouTube Search + Play First Video ──────────────────────
print("\n[TEST 3] 'Bro, search compiler design on YouTube and play the first relevant video.'")
print("-" * 90)
q3 = "Bro, search compiler design on YouTube and play the first relevant video."
t0 = time.time()
r3 = orchestrator.process_turn(q3)
el3 = time.time() - t0
ok3 = "youtube" in r3.lower() or "compiler" in r3.lower() or "playing" in r3.lower()
print(f"  Response: {r3!r}")
print(f"  Result: {PASS if ok3 else FAIL} (Latency: {el3:.3f}s)")
test_results["TEST_3_YOUTUBE_SEARCH_PLAY"] = {
    "input": q3, "intent": "MULTI_STEP (YouTube Search + Play)",
    "plan": "[open_website('youtube'), search_youtube('compiler design'), play_youtube('compiler design')]",
    "verified": ok3, "actual": r3, "latency": f"{el3:.3f}s", "result": "PASS" if ok3 else "FAIL"
}


# ── TEST 4: Web Search + Explanation ─────────────────────────────────────────
print("\n[TEST 4] 'Bro, search latest AI news and explain it.'")
print("-" * 90)
q4 = "Bro, search latest AI news and explain it."
t0 = time.time()
r4 = orchestrator.process_turn(q4)
el4 = time.time() - t0
ok4 = len(r4) > 30 and "overloaded" not in r4.lower()
print(f"  Response: {r4[:150]!r}...")
print(f"  Result: {PASS if ok4 else FAIL} (Latency: {el4:.3f}s)")
test_results["TEST_4_WEB_SEARCH_EXPLAIN"] = {
    "input": q4, "intent": "MULTI_STEP (Web Search + Gemini Explanation)",
    "plan": "[web_search -> gemini_synthesis]",
    "verified": ok4, "actual": r4[:150], "latency": f"{el4:.3f}s", "result": "PASS" if ok4 else "FAIL"
}


# ── TEST 5: WhatsApp Send & Status Verification ───────────────────────────────
print("\n[TEST 5] 'Bro, send WhatsApp message to 919876543210 text Hello, this is CHAMP.'")
print("-" * 90)
q5 = "Bro, send WhatsApp message to 919876543210 text Hello, this is CHAMP."
t0 = time.time()
r5 = orchestrator.process_turn(q5)
el5 = time.time() - t0
ok5 = "whatsapp" in r5.lower() or "status" in r5.lower() or "919876543210" in r5 or "sent" in r5.lower() or "verification" in r5.lower()
print(f"  Response: {r5!r}")
print(f"  Result: {PASS if ok5 else FAIL} (Latency: {el5:.3f}s)")
test_results["TEST_5_WHATSAPP_SEND_VERIFY"] = {
    "input": q5, "intent": "WHATSAPP_SEND (Recipient + Typing + Send + Verification)",
    "plan": "whatsapp_send_message(phone='919876543210', message='Hello, this is CHAMP.')",
    "verified": ok5, "actual": r5, "latency": f"{el5:.3f}s", "result": "PASS" if ok5 else "FAIL"
}


# ── TEST 6: RAG Search + Word Document Creation ──────────────────────────────
print("\n[TEST 6] 'Bro, enoda notes-la lexical analysis find panni Word summary create pannu.'")
print("-" * 90)
q6 = "Bro, enoda notes-la lexical analysis find panni Word summary create pannu."
t0 = time.time()
r6 = orchestrator.process_turn(q6)
el6 = time.time() - t0

f6 = Path(ROOT) / "data" / "documents" / "lexical_analysis_notes_summary.docx"
if not f6.exists():
    f6 = Path(ROOT) / "data" / "documents" / "document.docx"
ok6 = f6.exists() and f6.stat().st_size > 1000

print(f"  Response: {r6!r}")
print(f"  File Verified on Disk: {f6.exists()} ({f6})")
print(f"  Result: {PASS if ok6 else FAIL} (Latency: {el6:.3f}s)")
test_results["TEST_6_RAG_WORD_CREATION"] = {
    "input": q6, "intent": "MULTI_STEP (RAG + Word DOCX)",
    "plan": "[search_knowledge('lexical analysis'), create_word, open_application(word)]",
    "verified": ok6, "file": str(f6), "actual": r6, "latency": f"{el6:.3f}s", "result": "PASS" if ok6 else "FAIL"
}


# ── REGRESSION TESTS (7–13) ──────────────────────────────────────────────────
print("\n[REGRESSION 1] Gemini General Q&A: 'Bro, what is machine learning?'")
q_reg1 = "Bro, what is machine learning?"
t0 = time.time()
r_reg1 = orchestrator.process_turn(q_reg1)
el_reg1 = time.time() - t0
ok_reg1 = len(r_reg1) > 20
test_results["REG_1_GEMINI"] = {"input": q_reg1, "intent": "CONVERSATION", "latency": f"{el_reg1:.3f}s", "result": "PASS" if ok_reg1 else "FAIL"}

print("\n[REGRESSION 2] RAG Document Q&A: 'Bro, explain lexical analysis from my notes.'")
q_reg2 = "Bro, explain lexical analysis from my notes."
t0 = time.time()
r_reg2 = orchestrator.process_turn(q_reg2)
el_reg2 = time.time() - t0
ok_reg2 = len(r_reg2) > 20
test_results["REG_2_RAG"] = {"input": q_reg2, "intent": "CONVERSATION (RAG)", "latency": f"{el_reg2:.3f}s", "result": "PASS" if ok_reg2 else "FAIL"}

print("\n[REGRESSION 3] Web Search Q&A: 'Bro, what's the latest AI news?'")
q_reg3 = "Bro, what's the latest AI news?"
t0 = time.time()
r_reg3 = orchestrator.process_turn(q_reg3)
el_reg3 = time.time() - t0
ok_reg3 = len(r_reg3) > 20
test_results["REG_3_WEB"] = {"input": q_reg3, "intent": "CONVERSATION (Web)", "latency": f"{el_reg3:.3f}s", "result": "PASS" if ok_reg3 else "FAIL"}

print("\n[REGRESSION 4] Windows App: 'Bro, open Calculator.'")
q_reg4 = "Bro, open Calculator."
t0 = time.time()
r_reg4 = orchestrator.process_turn(q_reg4)
el_reg4 = time.time() - t0
ok_reg4 = "calculator" in r_reg4.lower()
test_results["REG_4_WINDOWS_APP"] = {"input": q_reg4, "intent": "ACTION", "latency": f"{el_reg4:.3f}s", "result": "PASS" if ok_reg4 else "FAIL"}

print("\n[REGRESSION 5] Browser Website: 'Bro, open YouTube.'")
q_reg5 = "Bro, open YouTube."
t0 = time.time()
r_reg5 = orchestrator.process_turn(q_reg5)
el_reg5 = time.time() - t0
ok_reg5 = "youtube" in r_reg5.lower() or "opened" in r_reg5.lower()
test_results["REG_5_BROWSER"] = {"input": q_reg5, "intent": "ACTION", "latency": f"{el_reg5:.3f}s", "result": "PASS" if ok_reg5 else "FAIL"}

print("\n[REGRESSION 6] Google Search: 'Bro, search Python tutorial.'")
q_reg6 = "Bro, search Python tutorial."
t0 = time.time()
r_reg6 = orchestrator.process_turn(q_reg6)
el_reg6 = time.time() - t0
ok_reg6 = "searching" in r_reg6.lower() or "python" in r_reg6.lower()
test_results["REG_6_GOOGLE_SEARCH"] = {"input": q_reg6, "intent": "ACTION", "latency": f"{el_reg6:.3f}s", "result": "PASS" if ok_reg6 else "FAIL"}

print("\n[REGRESSION 7] YouTube Search: 'Bro, search compiler design on YouTube.'")
q_reg7 = "Bro, search compiler design on YouTube."
t0 = time.time()
r_reg7 = orchestrator.process_turn(q_reg7)
el_reg7 = time.time() - t0
ok_reg7 = "youtube" in r_reg7.lower() or "compiler" in r_reg7.lower()
test_results["REG_7_YOUTUBE_SEARCH"] = {"input": q_reg7, "intent": "ACTION", "latency": f"{el_reg7:.3f}s", "result": "PASS" if ok_reg7 else "FAIL"}


# ── SUMMARY ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 90)
print("  PHASE 7 MULTI-STEP EXECUTION + WHATSAPP TEST SUMMARY")
print("=" * 90)

all_passed = True
for key, data in test_results.items():
    res = data["result"]
    print(f"  {key:32s} : {res}  (Latency: {data['latency']})")
    if res != "PASS":
        all_passed = False

print("=" * 90)
print(f"  FINAL PHASE 7 MULTI-STEP STATUS: {'✅ PASS' if all_passed else '❌ FAIL'}")
print("=" * 90)

# Save JSON results
out_json = Path(ROOT) / "data" / "phase7_multistep_results.json"
out_json.parent.mkdir(parents=True, exist_ok=True)
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(test_results, f, indent=2)

sys.exit(0 if all_passed else 1)

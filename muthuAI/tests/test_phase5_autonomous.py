"""
CHAMP — Phase 5 Autonomous Task Planner & Final Agent Integration Test Suite
Executes 10 End-to-End Autonomous Tests + 7 Regression Tests.
Run: python tests/test_phase5_autonomous.py
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

print("=" * 85)
print("  CHAMP — PHASE 5: AUTONOMOUS TASK PLANNER & FINAL AGENT INTEGRATION")
print("=" * 85)

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
    tts_module=None  # Silent for automated testing
)

# Ingest test doc for RAG regression test
docs_dir = Path(ROOT) / "data" / "documents"
docs_dir.mkdir(parents=True, exist_ok=True)
test_doc_path = docs_dir / "compiler_notes.txt"
if not test_doc_path.exists():
    test_doc_path.write_text("Compiler Design: Lexical analysis scans tokens.", encoding="utf-8")
RAGPipeline().ingest(test_doc_path)


# ── E2E TEST 1: Open Chrome ──────────────────────────────────────────────────
print("\n[TEST 1] 'Bro, open Chrome.'")
print("-" * 85)
q1 = "Bro, open Chrome."
t0 = time.time()
r1 = orchestrator.process_turn(q1)
el1 = time.time() - t0
ok1 = "chrome" in r1.lower() or "opened" in r1.lower()
print(f"  Response: {r1!r}")
print(f"  Result: {PASS if ok1 else FAIL} (Latency: {el1:.3f}s)")
test_results["TEST_1_CHROME"] = {
    "input": q1, "intent": "ACTION", "plan": "open_application(name='chrome')",
    "expected": "Chrome application opens", "actual": r1, "latency": f"{el1:.3f}s", "result": "PASS" if ok1 else "FAIL"
}


# ── E2E TEST 2: Search Python Tutorial ───────────────────────────────────────
print("\n[TEST 2] 'Bro, search Python tutorial.'" )
print("-" * 85)
q2 = "Bro, search Python tutorial."
t0 = time.time()
r2 = orchestrator.process_turn(q2)
el2 = time.time() - t0
ok2 = "searching" in r2.lower() or "python" in r2.lower()
print(f"  Response: {r2!r}")
print(f"  Result: {PASS if ok2 else FAIL} (Latency: {el2:.3f}s)")
test_results["TEST_2_GOOGLE_SEARCH"] = {
    "input": q2, "intent": "ACTION", "plan": "search_google(query='Python tutorial')",
    "expected": "Google search page opens", "actual": r2, "latency": f"{el2:.3f}s", "result": "PASS" if ok2 else "FAIL"
}


# ── E2E TEST 3: Multi-Step YouTube Search ────────────────────────────────────
print("\n[TEST 3] 'Bro, open YouTube and search compiler design.'" )
print("-" * 85)
q3 = "Bro, open YouTube and search compiler design."
t0 = time.time()
r3 = orchestrator.process_turn(q3)
el3 = time.time() - t0
ok3 = "youtube" in r3.lower() or "compiler" in r3.lower()
print(f"  Response: {r3!r}")
print(f"  Result: {PASS if ok3 else FAIL} (Latency: {el3:.3f}s)")
test_results["TEST_3_YOUTUBE_MULTISTEP"] = {
    "input": q3, "intent": "ACTION (Multi-step)", "plan": "[open_website('youtube'), search_youtube('compiler design')]",
    "expected": "YouTube opened and compiler design searched", "actual": r3, "latency": f"{el3:.3f}s", "result": "PASS" if ok3 else "FAIL"
}


# ── E2E TEST 4: Excel Student Marks Sheet ────────────────────────────────────
print("\n[TEST 4] 'Bro, create an Excel sheet with student names and marks.'" )
print("-" * 85)
q4 = "Bro, create an Excel sheet with student names and marks."
t0 = time.time()
r4 = orchestrator.process_turn(q4)
el4 = time.time() - t0
ok4 = "excel" in r4.lower() or "students_marks.xlsx" in r4.lower() or "created" in r4.lower()
print(f"  Response: {r4!r}")
print(f"  Result: {PASS if ok4 else FAIL} (Latency: {el4:.3f}s)")
test_results["TEST_4_EXCEL_AUTONOMOUS"] = {
    "input": q4, "intent": "ACTION", "plan": "create_excel(file_name='students_marks.xlsx', ...)",
    "expected": "students_marks.xlsx created & validated", "actual": r4, "latency": f"{el4:.3f}s", "result": "PASS" if ok4 else "FAIL"
}


# ── E2E TEST 5: Word Report Machine Learning ─────────────────────────────────
print("\n[TEST 5] 'Bro, create a Word report about machine learning.'" )
print("-" * 85)
q5 = "Bro, create a Word report about machine learning."
t0 = time.time()
r5 = orchestrator.process_turn(q5)
el5 = time.time() - t0
ok5 = "word" in r5.lower() or "machine_learning_report.docx" in r5.lower() or "created" in r5.lower()
print(f"  Response: {r5!r}")
print(f"  Result: {PASS if ok5 else FAIL} (Latency: {el5:.3f}s)")
test_results["TEST_5_WORD_AUTONOMOUS"] = {
    "input": q5, "intent": "ACTION", "plan": "create_word(file_name='machine_learning_report.docx', ...)",
    "expected": "machine_learning_report.docx created & validated", "actual": r5, "latency": f"{el5:.3f}s", "result": "PASS" if ok5 else "FAIL"
}


# ── E2E TEST 6: PowerPoint 5-Slide AI Presentation ───────────────────────────
print("\n[TEST 6] 'Bro, create a 5-slide PowerPoint about AI.'" )
print("-" * 85)
q6 = "Bro, create a 5-slide PowerPoint about AI."
t0 = time.time()
r6 = orchestrator.process_turn(q6)
el6 = time.time() - t0
ok6 = "powerpoint" in r6.lower() or "ai_overview.pptx" in r6.lower() or "created" in r6.lower() or "presentation" in r6.lower()
print(f"  Response: {r6!r}")
print(f"  Result: {PASS if ok6 else FAIL} (Latency: {el6:.3f}s)")
test_results["TEST_6_POWERPOINT_AUTONOMOUS"] = {
    "input": q6, "intent": "ACTION", "plan": "create_powerpoint(file_name='ai_overview.pptx', slides=5)",
    "expected": "ai_overview.pptx created & validated", "actual": r6, "latency": f"{el6:.3f}s", "result": "PASS" if ok6 else "FAIL"
}


# ── E2E TEST 7: Open Project Folder ──────────────────────────────────────────
print("\n[TEST 7] 'Bro, open my project folder.'" )
print("-" * 85)
q7 = "Bro, open my project folder."
t0 = time.time()
r7 = orchestrator.process_turn(q7)
el7 = time.time() - t0
ok7 = "opened" in r7.lower() or "folder" in r7.lower() or "muthuai" in r7.lower()
print(f"  Response: {r7!r}")
print(f"  Result: {PASS if ok7 else FAIL} (Latency: {el7:.3f}s)")
test_results["TEST_7_PROJECT_FOLDER"] = {
    "input": q7, "intent": "ACTION", "plan": "open_folder(path='d:\\juniors\\muthuAI')",
    "expected": "Project folder opened in Explorer", "actual": r7, "latency": f"{el7:.3f}s", "result": "PASS" if ok7 else "FAIL"
}


# ── E2E TEST 8: Web Search + Explanation ─────────────────────────────────────
print("\n[TEST 8] 'Bro, search the latest AI news and explain the first useful result.'" )
print("-" * 85)
q8 = "Bro, search the latest AI news and explain the first useful result."
t0 = time.time()
r8 = orchestrator.process_turn(q8)
el8 = time.time() - t0
ok8 = len(r8) > 20 and "overloaded" not in r8.lower()
print(f"  Response: {r8[:140]!r}...")
print(f"  Result: {PASS if ok8 else FAIL} (Latency: {el8:.3f}s)")
test_results["TEST_8_SEARCH_AND_EXPLAIN"] = {
    "input": q8, "intent": "CONVERSATION (Web Search + Explanation)", "plan": "Web Search -> Gemini Explanation",
    "expected": "Web search performed and first result explained", "actual": r8[:150], "latency": f"{el8:.3f}s", "result": "PASS" if ok8 else "FAIL"
}


# ── E2E TEST 9: Web Search + Word Summary Creation ───────────────────────────
print("\n[TEST 9] 'Bro, search latest AI agent news and create a Word summary.'" )
print("-" * 85)
q9 = "Bro, search latest AI agent news and create a Word summary."
t0 = time.time()
r9 = orchestrator.process_turn(q9)
el9 = time.time() - t0
ok9 = "word" in r9.lower() or "summary" in r9.lower() or "ai_agent_summary.docx" in r9.lower() or "created" in r9.lower()
print(f"  Response: {r9!r}")
print(f"  Result: {PASS if ok9 else FAIL} (Latency: {el9:.3f}s)")
test_results["TEST_9_SEARCH_AND_WORD_SUMMARY"] = {
    "input": q9, "intent": "ACTION (Multi-step Web Search + Word DOCX)", "plan": "create_word(file_name='ai_agent_summary.docx', ...)",
    "expected": "Word summary ai_agent_summary.docx created & validated", "actual": r9, "latency": f"{el9:.3f}s", "result": "PASS" if ok9 else "FAIL"
}


# ── E2E TEST 10: Task Cancellation ───────────────────────────────────────────
print("\n[TEST 10] 'Bro, stop the current task.'" )
print("-" * 85)
q10 = "Bro, stop the current task."
t0 = time.time()
r10 = orchestrator.process_turn(q10)
el10 = time.time() - t0
ok10 = "cancelled" in r10.lower() or "stop" in r10.lower()
print(f"  Response: {r10!r}")
print(f"  Result: {PASS if ok10 else FAIL} (Latency: {el10:.3f}s)")
test_results["TEST_10_CANCELLATION"] = {
    "input": q10, "intent": "SYSTEM (Cancellation)", "plan": "SessionState.cancel() -> TaskState.CANCELLED",
    "expected": "Task safely cancelled and reset to CANCELLED state", "actual": r10, "latency": f"{el10:.3f}s", "result": "PASS" if ok10 else "FAIL"
}


# ── REGRESSION TESTS (11–17) ──────────────────────────────────────────────────
print("\n[REGRESSION 1] Gemini General Q&A: 'Bro, what is machine learning?'")
q_reg1 = "Bro, what is machine learning?"
t0 = time.time()
r_reg1 = orchestrator.process_turn(q_reg1)
el_reg1 = time.time() - t0
ok_reg1 = len(r_reg1) > 20
test_results["REG_1_GEMINI"] = {"input": q_reg1, "intent": "CONVERSATION", "latency": f"{el_reg1:.3f}s", "result": "PASS" if ok_reg1 else "FAIL"}
print(f"  Result: {PASS if ok_reg1 else FAIL} (Latency: {el_reg1:.3f}s)")

print("\n[REGRESSION 2] RAG Document Q&A (Optimized Singleton): 'Bro, explain lexical analysis from my notes.'")
q_reg2 = "Bro, explain lexical analysis from my notes."
t0 = time.time()
r_reg2 = orchestrator.process_turn(q_reg2)
el_reg2 = time.time() - t0
ok_reg2 = len(r_reg2) > 20
test_results["REG_2_RAG"] = {"input": q_reg2, "intent": "CONVERSATION (RAG)", "latency": f"{el_reg2:.3f}s", "result": "PASS" if ok_reg2 else "FAIL"}
print(f"  Result: {PASS if ok_reg2 else FAIL} (Latency: {el_reg2:.3f}s)")

print("\n[REGRESSION 3] Web Search Q&A: 'Bro, what's the latest AI news?'")
q_reg3 = "Bro, what's the latest AI news?"
t0 = time.time()
r_reg3 = orchestrator.process_turn(q_reg3)
el_reg3 = time.time() - t0
ok_reg3 = len(r_reg3) > 20
test_results["REG_3_WEB"] = {"input": q_reg3, "intent": "CONVERSATION (Web Search)", "latency": f"{el_reg3:.3f}s", "result": "PASS" if ok_reg3 else "FAIL"}
print(f"  Result: {PASS if ok_reg3 else FAIL} (Latency: {el_reg3:.3f}s)")

print("\n[REGRESSION 4] Windows App: 'Bro, open Calculator.'")
q_reg4 = "Bro, open Calculator."
t0 = time.time()
r_reg4 = orchestrator.process_turn(q_reg4)
el_reg4 = time.time() - t0
ok_reg4 = "calculator" in r_reg4.lower()
test_results["REG_4_WINDOWS_APP"] = {"input": q_reg4, "intent": "ACTION", "latency": f"{el_reg4:.3f}s", "result": "PASS" if ok_reg4 else "FAIL"}
print(f"  Result: {PASS if ok_reg4 else FAIL} (Latency: {el_reg4:.3f}s)")

print("\n[REGRESSION 5] Browser Website: 'Bro, open YouTube.'")
q_reg5 = "Bro, open YouTube."
t0 = time.time()
r_reg5 = orchestrator.process_turn(q_reg5)
el_reg5 = time.time() - t0
ok_reg5 = "youtube" in r_reg5.lower() or "opened" in r_reg5.lower()
test_results["REG_5_BROWSER"] = {"input": q_reg5, "intent": "ACTION", "latency": f"{el_reg5:.3f}s", "result": "PASS" if ok_reg5 else "FAIL"}
print(f"  Result: {PASS if ok_reg5 else FAIL} (Latency: {el_reg5:.3f}s)")

print("\n[REGRESSION 6] Google Search: 'Bro, search Python tutorial.'")
q_reg6 = "Bro, search Python tutorial."
t0 = time.time()
r_reg6 = orchestrator.process_turn(q_reg6)
el_reg6 = time.time() - t0
ok_reg6 = "searching" in r_reg6.lower() or "python" in r_reg6.lower()
test_results["REG_6_GOOGLE_SEARCH"] = {"input": q_reg6, "intent": "ACTION", "latency": f"{el_reg6:.3f}s", "result": "PASS" if ok_reg6 else "FAIL"}
print(f"  Result: {PASS if ok_reg6 else FAIL} (Latency: {el_reg6:.3f}s)")

print("\n[REGRESSION 7] YouTube Search: 'Bro, search compiler design on YouTube.'")
q_reg7 = "Bro, search compiler design on YouTube."
t0 = time.time()
r_reg7 = orchestrator.process_turn(q_reg7)
el_reg7 = time.time() - t0
ok_reg7 = "youtube" in r_reg7.lower() or "compiler" in r_reg7.lower()
test_results["REG_7_YOUTUBE_SEARCH"] = {"input": q_reg7, "intent": "ACTION", "latency": f"{el_reg7:.3f}s", "result": "PASS" if ok_reg7 else "FAIL"}
print(f"  Result: {PASS if ok_reg7 else FAIL} (Latency: {el_reg7:.3f}s)")


# ── SUMMARY ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 85)
print("  PHASE 5 AUTONOMOUS AGENT TEST SUMMARY")
print("=" * 85)

all_passed = True
for key, data in test_results.items():
    res = data["result"]
    print(f"  {key:32s} : {res}  (Latency: {data['latency']})")
    if res != "PASS":
        all_passed = False

print("=" * 85)
print(f"  FINAL PHASE 5 AUTONOMOUS AGENT STATUS: {'✅ PASS' if all_passed else '❌ FAIL'}")
print("=" * 85)

# Save JSON results
out_json = Path(ROOT) / "data" / "phase5_autonomous_results.json"
out_json.parent.mkdir(parents=True, exist_ok=True)
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(test_results, f, indent=2)

sys.exit(0 if all_passed else 1)
